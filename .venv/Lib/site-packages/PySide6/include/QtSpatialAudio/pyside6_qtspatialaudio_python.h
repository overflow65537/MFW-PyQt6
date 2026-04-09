// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTSPATIALAUDIO_PYTHON_H
#define SBK_QTSPATIALAUDIO_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtnetwork_python.h>
#include <pyside6_qtmultimedia_python.h>

// Bound library includes
#include <QtSpatialAudio/qambientsound.h>
#include <QtSpatialAudio/qaudioengine.h>
#include <QtSpatialAudio/qaudioroom.h>
#include <QtSpatialAudio/qspatialsound.h>

QT_BEGIN_NAMESPACE
class QAudioListener;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAmbientSound_Loops_IDX                              = 1,
    SBK_QAmbientSound_IDX                                    = 0,
    SBK_QAudioEngine_OutputMode_IDX                          = 3,
    SBK_QAudioEngine_IDX                                     = 2,
    SBK_QAudioListener_IDX                                   = 4,
    SBK_QAudioRoom_Material_IDX                              = 6,
    SBK_QAudioRoom_Wall_IDX                                  = 7,
    SBK_QAudioRoom_IDX                                       = 5,
    SBK_QSpatialSound_Loops_IDX                              = 10,
    SBK_QSpatialSound_DistanceModel_IDX                      = 9,
    SBK_QSpatialSound_IDX                                    = 8,
    SBK_QtSpatialAudio_IDX_COUNT                             = 11,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtSpatialAudioTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtSpatialAudioModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtSpatialAudioTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTSPATIALAUDIO_QLIST_INT_IDX                         = 0, // QList<int>
    SBK_QTSPATIALAUDIO_QLIST_QVARIANT_IDX                    = 1, // QList<QVariant>
    SBK_QTSPATIALAUDIO_QLIST_QSTRING_IDX                     = 2, // QList<QString>
    SBK_QTSPATIALAUDIO_QMAP_QSTRING_QVARIANT_IDX             = 3, // QMap<QString,QVariant>
    SBK_QTSPATIALAUDIO_CONVERTERS_IDX_COUNT                  = 4,
};

// Converter indices
enum : int {
    SBK_QtSpatialAudio_QList_int_IDX                         = 0, // QList<int>
    SBK_QtSpatialAudio_QList_QVariant_IDX                    = 1, // QList<QVariant>
    SBK_QtSpatialAudio_QList_QString_IDX                     = 2, // QList<QString>
    SBK_QtSpatialAudio_QMap_QString_QVariant_IDX             = 3, // QMap<QString,QVariant>
    SBK_QtSpatialAudio_CONVERTERS_IDX_COUNT                  = 4,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAmbientSound::Loops >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAmbientSound_Loops_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientSound >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAmbientSound_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioEngine::OutputMode >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAudioEngine_OutputMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioEngine >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAudioEngine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioListener >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAudioListener_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioRoom::Material >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAudioRoom_Material_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioRoom::Wall >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAudioRoom_Wall_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAudioRoom >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QAudioRoom_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSpatialSound::Loops >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QSpatialSound_Loops_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSpatialSound::DistanceModel >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QSpatialSound_DistanceModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSpatialSound >() { return Shiboken::Module::get(SbkPySide6_QtSpatialAudioTypeStructs[SBK_QSpatialSound_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTSPATIALAUDIO_PYTHON_H

