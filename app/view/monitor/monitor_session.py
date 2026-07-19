"""监控运行时：独立控制器连接、截图循环与帧队列。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Optional

from PIL import Image

from app.common.config import cfg
from app.core.runner.monitor_task import MonitorTask
from app.utils.logger import (
    logger,
    restore_asyncify_logging,
    restore_qasync_logging,
    suppress_asyncify_logging,
    suppress_qasync_logging,
)
from app.utils.screencap_lock import screencap_guard


class MonitorSession:
    """监控截图会话，由 MonitorInterface 独占使用。"""

    def __init__(
        self,
        monitor_task: MonitorTask,
        *,
        log_prefix: str = "Monitor",
        max_queue_size: int = 2,
    ) -> None:
        self.monitor_task = monitor_task
        self._log_prefix = log_prefix
        self._max_queue_size = max_queue_size

        self._monitoring_active = False
        self._monitor_loop_task: Optional[asyncio.Task] = None
        self._image_processing_task: Optional[asyncio.Task] = None
        self._image_queue: Optional[asyncio.Queue] = None

        self._on_frame: Optional[Callable[[Image.Image], None]] = None
        self._on_capture_failure_clear: Optional[Callable[[], None]] = None
        self._on_controller_disconnected: Optional[
            Callable[[], Awaitable[None] | None]
        ] = None

    @property
    def monitoring_active(self) -> bool:
        return self._monitoring_active

    def set_callbacks(
        self,
        *,
        on_frame: Callable[[Image.Image], None],
        on_capture_failure_clear: Optional[Callable[[], None]] = None,
        on_controller_disconnected: Optional[
            Callable[[], Awaitable[None] | None]
        ] = None,
    ) -> None:
        self._on_frame = on_frame
        self._on_capture_failure_clear = on_capture_failure_clear
        self._on_controller_disconnected = on_controller_disconnected

    def is_controller_connected(self) -> bool:
        controller = getattr(self.monitor_task.maafw, "controller", None)
        if controller is None:
            return False
        connected = getattr(controller, "connected", None)
        return connected is not False

    async def connect_controller(self) -> bool:
        return bool(await self.monitor_task._connect())

    def capture_frame(self) -> Image.Image:
        """在工作线程中调用：从监控专用控制器截取一帧。"""
        controller = getattr(self.monitor_task.maafw, "controller", None)
        if controller is None:
            raise RuntimeError("控制器尚未初始化，无法抓取画面")
        # 与任务流 screencap_test 等串行，避免原生截图缓冲并发访问崩溃
        with screencap_guard():
            raw_frame = controller.post_screencap().wait().get()
            if raw_frame is None:
                raise ValueError("采集返回空帧")
            frame = raw_frame.copy()
        return Image.fromarray(frame[..., ::-1])

    async def capture_frame_async(self) -> Image.Image:
        return await asyncio.to_thread(self.capture_frame)

    def _get_target_interval(self) -> float:
        fps = max(1, int(cfg.get(cfg.monitor_capture_fps)))
        return 1.0 / fps

    def start_loop(self) -> None:
        if self._monitor_loop_task and not self._monitor_loop_task.done():
            logger.debug(f"[{self._log_prefix}] 监控循环任务已存在，跳过启动")
            return
        if self._monitoring_active:
            logger.debug(f"[{self._log_prefix}] 监控已激活，跳过启动")
            return
        if self._on_frame is None:
            raise RuntimeError("MonitorSession 未设置 on_frame 回调")

        target_fps = max(1, int(cfg.get(cfg.monitor_capture_fps)))
        logger.info(
            f"[{self._log_prefix}] 开始启动监控循环，截图速率: {target_fps} FPS"
        )
        suppress_asyncify_logging()
        suppress_qasync_logging()
        self._monitoring_active = True
        try:
            self._image_queue = asyncio.Queue(maxsize=self._max_queue_size)
            self._image_processing_task = asyncio.create_task(
                self._image_processing_loop()
            )
            self._monitor_loop_task = asyncio.create_task(self._monitor_loop())
        except Exception:
            self._monitoring_active = False
            restore_asyncify_logging()
            restore_qasync_logging()
            raise

    def stop_loop(self) -> None:
        self._monitoring_active = False
        task = self._monitor_loop_task
        self._monitor_loop_task = None
        if task and not task.done():
            task.cancel()
        restore_asyncify_logging()
        restore_qasync_logging()

    def deactivate(self) -> None:
        """仅标记为非活跃，不取消循环任务。"""
        self._monitoring_active = False

    async def wait_for_image_processing_complete(self, timeout: float = 1.0) -> None:
        if self._image_processing_task and not self._image_processing_task.done():
            try:
                await asyncio.wait_for(self._image_processing_task, timeout=timeout)
            except asyncio.TimeoutError:
                if not self._image_processing_task.done():
                    self._image_processing_task.cancel()
                    try:
                        await self._image_processing_task
                    except asyncio.CancelledError:
                        pass
            except Exception:
                pass
        self._image_queue = None
        self._image_processing_task = None

    async def teardown_controller(self) -> None:
        try:
            await self.monitor_task.maafw.stop_task()
        except Exception as exc:
            logger.warning(f"[{self._log_prefix}] 停止监控任务时出错: {exc}")
        try:
            if self.monitor_task.maafw.controller:
                self.monitor_task.maafw.controller = None
        except Exception as exc:
            logger.warning(f"[{self._log_prefix}] 清除控制器引用时出错: {exc}")

    async def stop(self) -> None:
        self.stop_loop()
        await self.wait_for_image_processing_complete(timeout=1.0)
        await self.teardown_controller()

    async def run_startup_sequence(
        self,
        *,
        should_abort: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """连接控制器并启动监控循环，返回是否成功。"""
        if not self.is_controller_connected():
            logger.info(f"[{self._log_prefix}] 监控控制器未就绪，开始连接...")
            if should_abort and should_abort():
                return False
            if not await self.connect_controller():
                logger.warning(f"[{self._log_prefix}] 监控控制器连接失败")
                return False

        self.start_loop()
        await asyncio.sleep(0.1)
        if not self._monitoring_active:
            logger.error(f"[{self._log_prefix}] 监控循环启动失败")
            return False

        try:
            if not self.is_controller_connected():
                await self._handle_controller_disconnection()
                return False
            pil_image = await self.capture_frame_async()
            if pil_image and self._on_frame:
                self._on_frame(pil_image)
        except Exception as exc:
            logger.warning(f"[{self._log_prefix}] 捕获第一帧失败: {exc}")

        return True

    async def _monitor_loop(self) -> None:
        loop = asyncio.get_running_loop()
        frame_count = 0
        logger.info(f"[{self._log_prefix}] 监控循环已开始运行")
        try:
            while self._monitoring_active:
                start = loop.time()
                if not self.is_controller_connected():
                    logger.warning(
                        f"[{self._log_prefix}] 监控循环中检测到控制器断开"
                    )
                    await self._handle_controller_disconnection()
                    return
                try:
                    pil_image = await asyncio.to_thread(self.capture_frame)
                except Exception as exc:
                    logger.warning(f"[{self._log_prefix}] 捕获帧失败: {exc}")
                    pil_image = None

                if pil_image and self._image_queue is not None:
                    frame_count += 1
                    try:
                        if self._image_queue.full():
                            try:
                                self._image_queue.get_nowait()
                            except asyncio.QueueEmpty:
                                pass
                        self._image_queue.put_nowait(pil_image)
                    except asyncio.QueueFull:
                        pass
                elif not pil_image and self._on_capture_failure_clear:
                    self._on_capture_failure_clear()

                elapsed = loop.time() - start
                wait = max(0, self._get_target_interval() - elapsed)
                await asyncio.sleep(wait)
        except asyncio.CancelledError:
            logger.info(
                f"[{self._log_prefix}] 监控循环被取消，共捕获 {frame_count} 帧"
            )
        finally:
            logger.info(
                f"[{self._log_prefix}] 监控循环结束，共捕获 {frame_count} 帧"
            )
            self._monitor_loop_task = None
            restore_asyncify_logging()
            restore_qasync_logging()

    async def _image_processing_loop(self) -> None:
        try:
            while self._monitoring_active or (
                self._image_queue and not self._image_queue.empty()
            ):
                if self._image_queue is None:
                    break
                try:
                    pil_image = await asyncio.wait_for(
                        self._image_queue.get(),
                        timeout=0.1,
                    )
                    if pil_image and self._on_frame:
                        self._on_frame(pil_image)
                except asyncio.TimeoutError:
                    continue
                except Exception as exc:
                    logger.warning(
                        f"[{self._log_prefix}] 处理预览帧失败: {exc}"
                    )
        except asyncio.CancelledError:
            pass
        finally:
            self._image_processing_task = None

    async def _handle_controller_disconnection(self) -> None:
        if not self._monitoring_active:
            return
        self._monitoring_active = False
        if self._on_controller_disconnected:
            result = self._on_controller_disconnected()
            if asyncio.iscoroutine(result):
                await result
