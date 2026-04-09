// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTSTATEMACHINE_PYTHON_H
#define SBK_QTSTATEMACHINE_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtStateMachine/qabstracttransition.h>
#include <QtStateMachine/qhistorystate.h>
#include <QtStateMachine/qstate.h>
#include <QtStateMachine/qstatemachine.h>

QT_BEGIN_NAMESPACE
class QAbstractState;
class QEventTransition;
class QFinalState;
class QKeyEventTransition;
class QMouseEventTransition;
class QSignalTransition;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractState_IDX                                   = 0,
    SBK_QAbstractTransition_TransitionType_IDX               = 2,
    SBK_QAbstractTransition_IDX                              = 1,
    SBK_QEventTransition_IDX                                 = 3,
    SBK_QFinalState_IDX                                      = 4,
    SBK_QHistoryState_HistoryType_IDX                        = 6,
    SBK_QHistoryState_IDX                                    = 5,
    SBK_QKeyEventTransition_IDX                              = 7,
    SBK_QMouseEventTransition_IDX                            = 8,
    SBK_QSignalTransition_IDX                                = 9,
    SBK_QState_ChildMode_IDX                                 = 11,
    SBK_QState_RestorePolicy_IDX                             = 12,
    SBK_QState_IDX                                           = 10,
    SBK_QStateMachine_EventPriority_IDX                      = 15,
    SBK_QStateMachine_Error_IDX                              = 14,
    SBK_QStateMachine_IDX                                    = 13,
    SBK_QStateMachine_SignalEvent_IDX                        = 16,
    SBK_QStateMachine_WrappedEvent_IDX                       = 17,
    SBK_QtStateMachine_IDX_COUNT                             = 18,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtStateMachineTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtStateMachineModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtStateMachineTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTSTATEMACHINE_QLIST_INT_IDX                         = 0, // QList<int>
    SBK_QTSTATEMACHINE_QLIST_QABSTRACTANIMATIONPTR_IDX       = 1, // QList<QAbstractAnimation*>
    SBK_QTSTATEMACHINE_QLIST_QABSTRACTSTATEPTR_IDX           = 2, // QList<QAbstractState*>
    SBK_QTSTATEMACHINE_QLIST_QABSTRACTTRANSITIONPTR_IDX      = 3, // QList<QAbstractTransition*>
    SBK_QTSTATEMACHINE_QSET_QABSTRACTSTATEPTR_IDX            = 4, // QSet<QAbstractState*>
    SBK_QTSTATEMACHINE_QLIST_QVARIANT_IDX                    = 5, // QList<QVariant>
    SBK_QTSTATEMACHINE_QLIST_QSTRING_IDX                     = 6, // QList<QString>
    SBK_QTSTATEMACHINE_QMAP_QSTRING_QVARIANT_IDX             = 7, // QMap<QString,QVariant>
    SBK_QTSTATEMACHINE_CONVERTERS_IDX_COUNT                  = 8,
};

// Converter indices
enum : int {
    SBK_QtStateMachine_QList_int_IDX                         = 0, // QList<int>
    SBK_QtStateMachine_QList_QAbstractAnimationPTR_IDX       = 1, // QList<QAbstractAnimation*>
    SBK_QtStateMachine_QList_QAbstractStatePTR_IDX           = 2, // QList<QAbstractState*>
    SBK_QtStateMachine_QList_QAbstractTransitionPTR_IDX      = 3, // QList<QAbstractTransition*>
    SBK_QtStateMachine_QSet_QAbstractStatePTR_IDX            = 4, // QSet<QAbstractState*>
    SBK_QtStateMachine_QList_QVariant_IDX                    = 5, // QList<QVariant>
    SBK_QtStateMachine_QList_QString_IDX                     = 6, // QList<QString>
    SBK_QtStateMachine_QMap_QString_QVariant_IDX             = 7, // QMap<QString,QVariant>
    SBK_QtStateMachine_CONVERTERS_IDX_COUNT                  = 8,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAbstractState >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QAbstractState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractTransition::TransitionType >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QAbstractTransition_TransitionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractTransition >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QAbstractTransition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QEventTransition >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QEventTransition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFinalState >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QFinalState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHistoryState::HistoryType >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QHistoryState_HistoryType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHistoryState >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QHistoryState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QKeyEventTransition >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QKeyEventTransition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMouseEventTransition >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QMouseEventTransition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSignalTransition >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QSignalTransition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QState::ChildMode >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QState_ChildMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QState::RestorePolicy >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QState_RestorePolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QState >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStateMachine::EventPriority >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QStateMachine_EventPriority_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStateMachine::Error >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QStateMachine_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStateMachine >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QStateMachine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStateMachine::SignalEvent >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QStateMachine_SignalEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStateMachine::WrappedEvent >() { return Shiboken::Module::get(SbkPySide6_QtStateMachineTypeStructs[SBK_QStateMachine_WrappedEvent_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTSTATEMACHINE_PYTHON_H

