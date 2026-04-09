// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QT3DINPUT_PYTHON_H
#define SBK_QT3DINPUT_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qt3dcore_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <Qt3DInput/qabstractactioninput.h>
#include <Qt3DInput/qaxisaccumulator.h>
#include <Qt3DInput/qmousedevice.h>
#include <Qt3DInput/qmouseevent.h>

QT_BEGIN_NAMESPACE

namespace Qt3DInput {
    class QAbstractActionInput;
    class QAbstractAxisInput;
    class QAbstractPhysicalDevice;
    class QAction;
    class QActionInput;
    class QAnalogAxisInput;
    class QAxis;
    class QAxisSetting;
    class QButtonAxisInput;
    class QInputAspect;
    class QInputChord;
    class QInputSequence;
    class QInputSettings;
    class QKeyEvent;
    class QKeyboardDevice;
    class QKeyboardHandler;
    class QLogicalDevice;
    class QMouseHandler;
}
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_Qt3DInputQt3DInput_IDX                               = 0,
    SBK_Qt3DInput_QAbstractActionInput_IDX                   = 1,
    SBK_Qt3DInput_QAbstractAxisInput_IDX                     = 2,
    SBK_Qt3DInput_QAbstractPhysicalDevice_IDX                = 3,
    SBK_Qt3DInput_QAction_IDX                                = 4,
    SBK_Qt3DInput_QActionInput_IDX                           = 5,
    SBK_Qt3DInput_QAnalogAxisInput_IDX                       = 6,
    SBK_Qt3DInput_QAxis_IDX                                  = 7,
    SBK_Qt3DInput_QAxisAccumulator_SourceAxisType_IDX        = 9,
    SBK_Qt3DInput_QAxisAccumulator_IDX                       = 8,
    SBK_Qt3DInput_QAxisSetting_IDX                           = 10,
    SBK_Qt3DInput_QButtonAxisInput_IDX                       = 11,
    SBK_Qt3DInput_QInputAspect_IDX                           = 12,
    SBK_Qt3DInput_QInputChord_IDX                            = 13,
    SBK_Qt3DInput_QInputSequence_IDX                         = 14,
    SBK_Qt3DInput_QInputSettings_IDX                         = 15,
    SBK_Qt3DInput_QKeyEvent_IDX                              = 16,
    SBK_Qt3DInput_QKeyboardDevice_IDX                        = 17,
    SBK_Qt3DInput_QKeyboardHandler_IDX                       = 18,
    SBK_Qt3DInput_QLogicalDevice_IDX                         = 19,
    SBK_Qt3DInput_QMouseDevice_Axis_IDX                      = 21,
    SBK_Qt3DInput_QMouseDevice_IDX                           = 20,
    SBK_Qt3DInput_QMouseEvent_Buttons_IDX                    = 23,
    SBK_Qt3DInput_QMouseEvent_Modifiers_IDX                  = 24,
    SBK_Qt3DInput_QMouseEvent_IDX                            = 22,
    SBK_Qt3DInput_QMouseHandler_IDX                          = 25,
    SBK_Qt3DInput_QWheelEvent_Buttons_IDX                    = 27,
    SBK_Qt3DInput_QWheelEvent_Modifiers_IDX                  = 28,
    SBK_Qt3DInput_QWheelEvent_IDX                            = 26,
    SBK_Qt3DInput_IDX_COUNT                                  = 29,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_Qt3DInputTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_Qt3DInputModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_Qt3DInputTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QT3DINPUT_QLIST_INT_IDX                              = 0, // QList<int>
    SBK_QT3DINPUT_QLIST_QT3DINPUT_QABSTRACTACTIONINPUTPTR_IDX = 1, // QList<Qt3DInput::QAbstractActionInput*>
    SBK_QT3DINPUT_QLIST_QT3DINPUT_QAXISSETTINGPTR_IDX        = 2, // QList<Qt3DInput::QAxisSetting*>
    SBK_QT3DINPUT_QLIST_QT3DINPUT_QABSTRACTAXISINPUTPTR_IDX  = 3, // QList<Qt3DInput::QAbstractAxisInput*>
    SBK_QT3DINPUT_STD_VECTOR_QSHAREDPOINTER_QT3DCORE_QASPECTJOB_IDX = 4, // std::vector<QSharedPointer<Qt3DCore::QAspectJob>>
    SBK_QT3DINPUT_QLIST_QT3DINPUT_QACTIONPTR_IDX             = 5, // QList<Qt3DInput::QAction*>
    SBK_QT3DINPUT_QLIST_QT3DINPUT_QAXISPTR_IDX               = 6, // QList<Qt3DInput::QAxis*>
    SBK_QT3DINPUT_QLIST_QVARIANT_IDX                         = 7, // QList<QVariant>
    SBK_QT3DINPUT_QLIST_QSTRING_IDX                          = 8, // QList<QString>
    SBK_QT3DINPUT_QMAP_QSTRING_QVARIANT_IDX                  = 9, // QMap<QString,QVariant>
    SBK_QT3DINPUT_CONVERTERS_IDX_COUNT                       = 10,
};

// Converter indices
enum : int {
    SBK_Qt3DInput_QList_int_IDX                              = 0, // QList<int>
    SBK_Qt3DInput_QList_Qt3DInput_QAbstractActionInputPTR_IDX = 1, // QList<Qt3DInput::QAbstractActionInput*>
    SBK_Qt3DInput_QList_Qt3DInput_QAxisSettingPTR_IDX        = 2, // QList<Qt3DInput::QAxisSetting*>
    SBK_Qt3DInput_QList_Qt3DInput_QAbstractAxisInputPTR_IDX  = 3, // QList<Qt3DInput::QAbstractAxisInput*>
    SBK_Qt3DInput_std_vector_QSharedPointer_Qt3DCore_QAspectJob_IDX = 4, // std::vector<QSharedPointer<Qt3DCore::QAspectJob>>
    SBK_Qt3DInput_QList_Qt3DInput_QActionPTR_IDX             = 5, // QList<Qt3DInput::QAction*>
    SBK_Qt3DInput_QList_Qt3DInput_QAxisPTR_IDX               = 6, // QList<Qt3DInput::QAxis*>
    SBK_Qt3DInput_QList_QVariant_IDX                         = 7, // QList<QVariant>
    SBK_Qt3DInput_QList_QString_IDX                          = 8, // QList<QString>
    SBK_Qt3DInput_QMap_QString_QVariant_IDX                  = 9, // QMap<QString,QVariant>
    SBK_Qt3DInput_CONVERTERS_IDX_COUNT                       = 10,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAbstractActionInput >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAbstractActionInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAbstractAxisInput >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAbstractAxisInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAbstractPhysicalDevice >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAbstractPhysicalDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAction >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAction_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QActionInput >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QActionInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAnalogAxisInput >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAnalogAxisInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAxis >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAxisAccumulator::SourceAxisType >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAxisAccumulator_SourceAxisType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAxisAccumulator >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAxisAccumulator_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QAxisSetting >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QAxisSetting_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QButtonAxisInput >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QButtonAxisInput_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QInputAspect >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QInputAspect_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QInputChord >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QInputChord_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QInputSequence >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QInputSequence_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QInputSettings >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QInputSettings_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QKeyEvent >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QKeyEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QKeyboardDevice >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QKeyboardDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QKeyboardHandler >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QKeyboardHandler_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QLogicalDevice >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QLogicalDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QMouseDevice::Axis >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QMouseDevice_Axis_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QMouseDevice >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QMouseDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QMouseEvent::Buttons >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QMouseEvent_Buttons_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QMouseEvent::Modifiers >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QMouseEvent_Modifiers_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QMouseEvent >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QMouseEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QMouseHandler >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QMouseHandler_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QWheelEvent::Buttons >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QWheelEvent_Buttons_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QWheelEvent::Modifiers >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QWheelEvent_Modifiers_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DInput::QWheelEvent >() { return Shiboken::Module::get(SbkPySide6_Qt3DInputTypeStructs[SBK_Qt3DInput_QWheelEvent_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QT3DINPUT_PYTHON_H

