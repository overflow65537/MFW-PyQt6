// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTMULTIMEDIA_PYTHON_H
#define SBK_QTMULTIMEDIA_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtnetwork_python.h>

// Bound library includes
#include <QtMultimedia/qabstractvideobuffer.h>
#include <QtMultimedia/qaudio.h>
#include <QtMultimedia/qaudiodecoder.h>
#include <QtMultimedia/qaudiodevice.h>
#include <QtMultimedia/qaudioformat.h>
#include <QtMultimedia/qcamera.h>
#include <QtMultimedia/qcameradevice.h>
#include <QtMultimedia/qimagecapture.h>
#include <QtMultimedia/qmediaformat.h>
#include <QtMultimedia/qmediametadata.h>
#include <QtMultimedia/qmediaplayer.h>
#include <QtMultimedia/qmediarecorder.h>
#include <QtMultimedia/qmediatimerange.h>
#include <QtMultimedia/qplaybackoptions.h>
#include <QtMultimedia/qscreencapture.h>
#include <QtMultimedia/qsoundeffect.h>
#include <QtMultimedia/qtvideo.h>
#include <QtMultimedia/qvideoframe.h>
#include <QtMultimedia/qvideoframeformat.h>
#include <QtMultimedia/qwavedecoder.h>
#include <QtMultimedia/qwindowcapture.h>

QT_BEGIN_NAMESPACE
class QAudioBuffer;
class QAudioBufferInput;
class QAudioBufferOutput;
class QAudioInput;
class QAudioOutput;
class QAudioSink;
class QAudioSource;
class QCameraFormat;
class QCapturableWindow;
class QMediaCaptureSession;
class QMediaDevices;
class QVideoFrameInput;
class QVideoSink;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractVideoBuffer_IDX                             = 0,
    SBK_QAbstractVideoBuffer_MapData_IDX                     = 1,
    SBK_QAudio_Error_IDX                                     = 3,
    SBK_QAudio_State_IDX                                     = 4,
    SBK_QAudio_VolumeScale_IDX                               = 5,
    SBK_QtMultimediaQAudio_IDX                               = 2,
    SBK_QAudioBuffer_IDX                                     = 6,
    SBK_QAudioBufferInput_IDX                                = 7,
    SBK_QAudioBufferOutput_IDX                               = 8,
    SBK_QAudioDecoder_Error_IDX                              = 10,
    SBK_QAudioDecoder_IDX                                    = 9,
    SBK_QAudioDevice_Mode_IDX                                = 12,
    SBK_QAudioDevice_IDX                                     = 11,
    SBK_QAudioFormat_SampleFormat_IDX                        = 16,
    SBK_QAudioFormat_AudioChannelPosition_IDX                = 14,
    SBK_QAudioFormat_ChannelConfig_IDX                       = 15,
    SBK_QAudioFormat_IDX                                     = 13,
    SBK_QAudioInput_IDX                                      = 17,
    SBK_QAudioOutput_IDX                                     = 18,
    SBK_QAudioSink_IDX                                       = 19,
    SBK_QAudioSource_IDX                                     = 20,
    SBK_QCamera_Error_IDX                                    = 22,
    SBK_QCamera_FocusMode_IDX                                = 26,
    SBK_QCamera_FlashMode_IDX                                = 25,
    SBK_QCamera_TorchMode_IDX                                = 27,
    SBK_QCamera_ExposureMode_IDX                             = 23,
    SBK_QCamera_WhiteBalanceMode_IDX                         = 28,
    SBK_QCamera_Feature_IDX                                  = 24,
    SBK_QFlags_QCamera_Feature_IDX                           = 33,
    SBK_QCamera_IDX                                          = 21,
    SBK_QCameraDevice_Position_IDX                           = 30,
    SBK_QCameraDevice_IDX                                    = 29,
    SBK_QCameraFormat_IDX                                    = 31,
    SBK_QCapturableWindow_IDX                                = 32,
    SBK_QImageCapture_Error_IDX                              = 36,
    SBK_QImageCapture_Quality_IDX                            = 38,
    SBK_QImageCapture_FileFormat_IDX                         = 37,
    SBK_QImageCapture_IDX                                    = 35,
    SBK_QMediaCaptureSession_IDX                             = 39,
    SBK_QMediaDevices_IDX                                    = 40,
    SBK_QMediaFormat_FileFormat_IDX                          = 44,
    SBK_QMediaFormat_AudioCodec_IDX                          = 42,
    SBK_QMediaFormat_VideoCodec_IDX                          = 46,
    SBK_QMediaFormat_ConversionMode_IDX                      = 43,
    SBK_QMediaFormat_ResolveFlags_IDX                        = 45,
    SBK_QMediaFormat_IDX                                     = 41,
    SBK_QMediaMetaData_Key_IDX                               = 48,
    SBK_QMediaMetaData_IDX                                   = 47,
    SBK_QMediaPlayer_PlaybackState_IDX                       = 54,
    SBK_QMediaPlayer_MediaStatus_IDX                         = 52,
    SBK_QMediaPlayer_Error_IDX                               = 50,
    SBK_QMediaPlayer_Loops_IDX                               = 51,
    SBK_QMediaPlayer_PitchCompensationAvailability_IDX       = 53,
    SBK_QMediaPlayer_IDX                                     = 49,
    SBK_QMediaRecorder_Quality_IDX                           = 58,
    SBK_QMediaRecorder_EncodingMode_IDX                      = 56,
    SBK_QMediaRecorder_RecorderState_IDX                     = 59,
    SBK_QMediaRecorder_Error_IDX                             = 57,
    SBK_QMediaRecorder_IDX                                   = 55,
    SBK_QMediaTimeRange_IDX                                  = 60,
    SBK_QMediaTimeRange_Interval_IDX                         = 61,
    SBK_QPlaybackOptions_PlaybackIntent_IDX                  = 63,
    SBK_QPlaybackOptions_IDX                                 = 62,
    SBK_QScreenCapture_Error_IDX                             = 65,
    SBK_QScreenCapture_IDX                                   = 64,
    SBK_QSoundEffect_Loop_IDX                                = 67,
    SBK_QSoundEffect_Status_IDX                              = 68,
    SBK_QSoundEffect_IDX                                     = 66,
    SBK_QVideoFrame_HandleType_IDX                           = 70,
    SBK_QVideoFrame_MapMode_IDX                              = 71,
    SBK_QVideoFrame_RotationAngle_IDX                        = 74,
    SBK_QVideoFrame_IDX                                      = 69,
    SBK_QVideoFrame_PaintOptions_PaintFlag_IDX               = 73,
    SBK_QFlags_QVideoFrame_PaintOptions_PaintFlag_IDX        = 34,
    SBK_QVideoFrame_PaintOptions_IDX                         = 72,
    SBK_QVideoFrameFormat_PixelFormat_IDX                    = 80,
    SBK_QVideoFrameFormat_Direction_IDX                      = 79,
    SBK_QVideoFrameFormat_YCbCrColorSpace_IDX                = 81,
    SBK_QVideoFrameFormat_ColorSpace_IDX                     = 77,
    SBK_QVideoFrameFormat_ColorTransfer_IDX                  = 78,
    SBK_QVideoFrameFormat_ColorRange_IDX                     = 76,
    SBK_QVideoFrameFormat_IDX                                = 75,
    SBK_QVideoFrameInput_IDX                                 = 82,
    SBK_QVideoSink_IDX                                       = 83,
    SBK_QWaveDecoder_IDX                                     = 84,
    SBK_QWindowCapture_Error_IDX                             = 86,
    SBK_QWindowCapture_IDX                                   = 85,
    SBK_QtAudio_Error_IDX                                    = 88,
    SBK_QtAudio_State_IDX                                    = 89,
    SBK_QtAudio_VolumeScale_IDX                              = 90,
    SBK_QtMultimediaQtAudio_IDX                              = 87,
    SBK_QtVideo_Rotation_IDX                                 = 92,
    SBK_QtMultimediaQtVideo_IDX                              = 91,
    SBK_QtMultimedia_IDX_COUNT                               = 93,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtMultimediaTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtMultimediaModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtMultimediaTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTMULTIMEDIA_QLIST_INT_IDX                           = 0, // QList<int>
    SBK_QTMULTIMEDIA_QLIST_QMEDIATIMERANGE_INTERVAL_IDX      = 1, // QList<QMediaTimeRange::Interval>
    SBK_QTMULTIMEDIA_QLIST_QMEDIAMETADATA_KEY_IDX            = 2, // QList<QMediaMetaData::Key>
    SBK_QTMULTIMEDIA_QHASH_QMEDIAMETADATA_KEY_QVARIANT_IDX   = 3, // QHash<QMediaMetaData::Key,QVariant>
    SBK_QTMULTIMEDIA_QLIST_QMEDIAFORMAT_AUDIOCODEC_IDX       = 4, // QList<QMediaFormat::AudioCodec>
    SBK_QTMULTIMEDIA_QLIST_QMEDIAFORMAT_FILEFORMAT_IDX       = 5, // QList<QMediaFormat::FileFormat>
    SBK_QTMULTIMEDIA_QLIST_QMEDIAFORMAT_VIDEOCODEC_IDX       = 6, // QList<QMediaFormat::VideoCodec>
    SBK_QTMULTIMEDIA_QLIST_QSIZE_IDX                         = 7, // QList<QSize>
    SBK_QTMULTIMEDIA_QLIST_QCAMERAFORMAT_IDX                 = 8, // QList<QCameraFormat>
    SBK_QTMULTIMEDIA_QLIST_QAUDIOFORMAT_SAMPLEFORMAT_IDX     = 9, // QList<QAudioFormat::SampleFormat>
    SBK_QTMULTIMEDIA_QLIST_QCAPTURABLEWINDOW_IDX             = 10, // QList<QCapturableWindow>
    SBK_QTMULTIMEDIA_QLIST_QAUDIODEVICE_IDX                  = 11, // QList<QAudioDevice>
    SBK_QTMULTIMEDIA_QLIST_QCAMERADEVICE_IDX                 = 12, // QList<QCameraDevice>
    SBK_QTMULTIMEDIA_QLIST_QIMAGECAPTURE_FILEFORMAT_IDX      = 13, // QList<QImageCapture::FileFormat>
    SBK_QTMULTIMEDIA_QLIST_QMEDIAMETADATA_IDX                = 14, // QList<QMediaMetaData>
    SBK_QTMULTIMEDIA_QLIST_QVARIANT_IDX                      = 15, // QList<QVariant>
    SBK_QTMULTIMEDIA_QLIST_QSTRING_IDX                       = 16, // QList<QString>
    SBK_QTMULTIMEDIA_QMAP_QSTRING_QVARIANT_IDX               = 17, // QMap<QString,QVariant>
    SBK_QTMULTIMEDIA_CONVERTERS_IDX_COUNT                    = 18,
};

// Converter indices
enum : int {
    SBK_QtMultimedia_QList_int_IDX                           = 0, // QList<int>
    SBK_QtMultimedia_QList_QMediaTimeRange_Interval_IDX      = 1, // QList<QMediaTimeRange::Interval>
    SBK_QtMultimedia_QList_QMediaMetaData_Key_IDX            = 2, // QList<QMediaMetaData::Key>
    SBK_QtMultimedia_QHash_QMediaMetaData_Key_QVariant_IDX   = 3, // QHash<QMediaMetaData::Key,QVariant>
    SBK_QtMultimedia_QList_QMediaFormat_AudioCodec_IDX       = 4, // QList<QMediaFormat::AudioCodec>
    SBK_QtMultimedia_QList_QMediaFormat_FileFormat_IDX       = 5, // QList<QMediaFormat::FileFormat>
    SBK_QtMultimedia_QList_QMediaFormat_VideoCodec_IDX       = 6, // QList<QMediaFormat::VideoCodec>
    SBK_QtMultimedia_QList_QSize_IDX                         = 7, // QList<QSize>
    SBK_QtMultimedia_QList_QCameraFormat_IDX                 = 8, // QList<QCameraFormat>
    SBK_QtMultimedia_QList_QAudioFormat_SampleFormat_IDX     = 9, // QList<QAudioFormat::SampleFormat>
    SBK_QtMultimedia_QList_QCapturableWindow_IDX             = 10, // QList<QCapturableWindow>
    SBK_QtMultimedia_QList_QAudioDevice_IDX                  = 11, // QList<QAudioDevice>
    SBK_QtMultimedia_QList_QCameraDevice_IDX                 = 12, // QList<QCameraDevice>
    SBK_QtMultimedia_QList_QImageCapture_FileFormat_IDX      = 13, // QList<QImageCapture::FileFormat>
    SBK_QtMultimedia_QList_QMediaMetaData_IDX                = 14, // QList<QMediaMetaData>
    SBK_QtMultimedia_QList_QVariant_IDX                      = 15, // QList<QVariant>
    SBK_QtMultimedia_QList_QString_IDX                       = 16, // QList<QString>
    SBK_QtMultimedia_QMap_QString_QVariant_IDX               = 17, // QMap<QString,QVariant>
    SBK_QtMultimedia_CONVERTERS_IDX_COUNT                    = 18,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAbstractVideoBuffer >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAbstractVideoBuffer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractVideoBuffer::MapData >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAbstractVideoBuffer_MapData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioBuffer >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioBuffer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioBufferInput >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioBufferInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioBufferOutput >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioBufferOutput_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioDecoder::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioDecoder_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioDecoder >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioDecoder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioDevice::Mode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioDevice_Mode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioDevice >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioFormat::SampleFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioFormat_SampleFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioFormat::AudioChannelPosition >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioFormat_AudioChannelPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioFormat::ChannelConfig >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioFormat_ChannelConfig_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioInput >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioOutput >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioOutput_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioSink >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioSink_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioSource >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QAudioSource_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera::FocusMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_FocusMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera::FlashMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_FlashMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera::TorchMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_TorchMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera::ExposureMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_ExposureMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera::WhiteBalanceMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_WhiteBalanceMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera::Feature >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_Feature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCamera::Feature> >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QFlags_QCamera_Feature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCamera >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCamera_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCameraDevice::Position >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCameraDevice_Position_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCameraDevice >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCameraDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCameraFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCameraFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCapturableWindow >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QCapturableWindow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QImageCapture::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QImageCapture_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QImageCapture::Quality >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QImageCapture_Quality_IDX]); }
template<> inline PyTypeObject *SbkType< ::QImageCapture::FileFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QImageCapture_FileFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QImageCapture >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QImageCapture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaCaptureSession >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaCaptureSession_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaDevices >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaDevices_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaFormat::FileFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaFormat_FileFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaFormat::AudioCodec >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaFormat_AudioCodec_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaFormat::VideoCodec >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaFormat_VideoCodec_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaFormat::ConversionMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaFormat_ConversionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaFormat::ResolveFlags >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaFormat_ResolveFlags_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaMetaData::Key >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaMetaData_Key_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaMetaData >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaMetaData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaPlayer::PlaybackState >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaPlayer_PlaybackState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaPlayer::MediaStatus >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaPlayer_MediaStatus_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaPlayer::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaPlayer_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaPlayer::Loops >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaPlayer_Loops_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaPlayer::PitchCompensationAvailability >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaPlayer_PitchCompensationAvailability_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaPlayer >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaPlayer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaRecorder::Quality >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaRecorder_Quality_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaRecorder::EncodingMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaRecorder_EncodingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaRecorder::RecorderState >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaRecorder_RecorderState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaRecorder::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaRecorder_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaRecorder >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaRecorder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaTimeRange >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaTimeRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMediaTimeRange::Interval >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QMediaTimeRange_Interval_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaybackOptions::PlaybackIntent >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QPlaybackOptions_PlaybackIntent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaybackOptions >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QPlaybackOptions_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScreenCapture::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QScreenCapture_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScreenCapture >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QScreenCapture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSoundEffect::Loop >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QSoundEffect_Loop_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSoundEffect::Status >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QSoundEffect_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSoundEffect >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QSoundEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrame::HandleType >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrame_HandleType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrame::MapMode >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrame_MapMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrame::RotationAngle >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrame_RotationAngle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrame >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrame_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrame::PaintOptions::PaintFlag >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrame_PaintOptions_PaintFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QVideoFrame::PaintOptions::PaintFlag> >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QFlags_QVideoFrame_PaintOptions_PaintFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrame::PaintOptions >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrame_PaintOptions_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameFormat::PixelFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameFormat_PixelFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameFormat::Direction >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameFormat_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameFormat::YCbCrColorSpace >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameFormat_YCbCrColorSpace_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameFormat::ColorSpace >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameFormat_ColorSpace_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameFormat::ColorTransfer >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameFormat_ColorTransfer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameFormat::ColorRange >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameFormat_ColorRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameFormat >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoFrameInput >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoFrameInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVideoSink >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QVideoSink_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWaveDecoder >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QWaveDecoder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWindowCapture::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QWindowCapture_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWindowCapture >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QWindowCapture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtAudio::Error >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QtAudio_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtAudio::State >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QtAudio_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtAudio::VolumeScale >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QtAudio_VolumeScale_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtVideo::Rotation >() { return Shiboken::Module::get(SbkPySide6_QtMultimediaTypeStructs[SBK_QtVideo_Rotation_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTMULTIMEDIA_PYTHON_H

