// @snippet qcpainterwidget-grabcanvas
Issues a texture readback request for ``canvas``. ``callback`` is invoked
either before the function returns, or later, depending on the underlying
``QRhi`` and 3D API implementation. Reading back texture contents may
involve a GPU->CPU copy, depending on the GPU architecture.
// @snippet qcpainterwidget-grabcanvas
