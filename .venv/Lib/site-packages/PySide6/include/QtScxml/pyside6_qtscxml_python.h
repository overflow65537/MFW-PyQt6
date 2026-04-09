// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTSCXML_PYTHON_H
#define SBK_QTSCXML_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtScxml/qscxmlcompiler.h>
#include <QtScxml/qscxmldatamodel.h>
#include <QtScxml/qscxmlevent.h>
#include <QtScxml/qscxmlexecutablecontent.h>

QT_BEGIN_NAMESPACE
class QScxmlCppDataModel;
class QScxmlDynamicScxmlServiceFactory;
class QScxmlError;
class QScxmlInvokableService;
class QScxmlInvokableServiceFactory;
class QScxmlNullDataModel;
class QScxmlStateMachine;
class QScxmlStaticScxmlServiceFactory;
class QScxmlTableData;

namespace QScxmlExecutableContent {
    struct AssignmentInfo;
    struct EvaluatorInfo;
    struct ForeachInfo;
    struct InvokeInfo;
    struct ParameterInfo;
}
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QScxmlCompiler_IDX                                   = 0,
    SBK_QScxmlCompiler_Loader_IDX                            = 1,
    SBK_QScxmlCppDataModel_IDX                               = 2,
    SBK_QScxmlDataModel_IDX                                  = 3,
    SBK_QScxmlDataModel_ForeachLoopBody_IDX                  = 4,
    SBK_QScxmlDynamicScxmlServiceFactory_IDX                 = 5,
    SBK_QScxmlError_IDX                                      = 6,
    SBK_QScxmlEvent_EventType_IDX                            = 8,
    SBK_QScxmlEvent_IDX                                      = 7,
    SBK_QtScxmlQScxmlExecutableContent_IDX                   = 9,
    SBK_QScxmlExecutableContent_AssignmentInfo_IDX           = 10,
    SBK_QScxmlExecutableContent_EvaluatorInfo_IDX            = 11,
    SBK_QScxmlExecutableContent_ForeachInfo_IDX              = 12,
    SBK_QScxmlExecutableContent_InvokeInfo_IDX               = 13,
    SBK_QScxmlExecutableContent_ParameterInfo_IDX            = 14,
    SBK_QScxmlInvokableService_IDX                           = 15,
    SBK_QScxmlInvokableServiceFactory_IDX                    = 16,
    SBK_QScxmlNullDataModel_IDX                              = 17,
    SBK_QScxmlStateMachine_IDX                               = 18,
    SBK_QScxmlStaticScxmlServiceFactory_IDX                  = 19,
    SBK_QScxmlTableData_IDX                                  = 20,
    SBK_QtScxml_IDX_COUNT                                    = 21,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtScxmlTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtScxmlModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtScxmlTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTSCXML_QLIST_INT_IDX                                = 0, // QList<int>
    SBK_QTSCXML_QLIST_QSCXMLERROR_IDX                        = 1, // QList<QScxmlError>
    SBK_QTSCXML_QMAP_QSTRING_QVARIANT_IDX                    = 2, // QMap<QString,QVariant>
    SBK_QTSCXML_QLIST_QSCXMLINVOKABLESERVICEPTR_IDX          = 3, // QList<QScxmlInvokableService*>
    SBK_QTSCXML_QLIST_QSCXMLEXECUTABLECONTENT_PARAMETERINFO_IDX = 4, // QList<QScxmlExecutableContent::ParameterInfo>
    SBK_QTSCXML_QLIST_QVARIANT_IDX                           = 5, // QList<QVariant>
    SBK_QTSCXML_QLIST_QSTRING_IDX                            = 6, // QList<QString>
    SBK_QTSCXML_CONVERTERS_IDX_COUNT                         = 7,
};

// Converter indices
enum : int {
    SBK_QtScxml_QList_int_IDX                                = 0, // QList<int>
    SBK_QtScxml_QList_QScxmlError_IDX                        = 1, // QList<QScxmlError>
    SBK_QtScxml_QMap_QString_QVariant_IDX                    = 2, // QMap<QString,QVariant>
    SBK_QtScxml_QList_QScxmlInvokableServicePTR_IDX          = 3, // QList<QScxmlInvokableService*>
    SBK_QtScxml_QList_QScxmlExecutableContent_ParameterInfo_IDX = 4, // QList<QScxmlExecutableContent::ParameterInfo>
    SBK_QtScxml_QList_QVariant_IDX                           = 5, // QList<QVariant>
    SBK_QtScxml_QList_QString_IDX                            = 6, // QList<QString>
    SBK_QtScxml_CONVERTERS_IDX_COUNT                         = 7,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QScxmlCompiler >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlCompiler_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlCompiler::Loader >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlCompiler_Loader_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlCppDataModel >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlCppDataModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlDataModel >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlDataModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlDataModel::ForeachLoopBody >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlDataModel_ForeachLoopBody_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlDynamicScxmlServiceFactory >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlDynamicScxmlServiceFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlError >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlEvent::EventType >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlEvent_EventType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlEvent >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlExecutableContent::AssignmentInfo >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlExecutableContent_AssignmentInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlExecutableContent::EvaluatorInfo >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlExecutableContent_EvaluatorInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlExecutableContent::ForeachInfo >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlExecutableContent_ForeachInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlExecutableContent::InvokeInfo >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlExecutableContent_InvokeInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlExecutableContent::ParameterInfo >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlExecutableContent_ParameterInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlInvokableService >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlInvokableService_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlInvokableServiceFactory >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlInvokableServiceFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlNullDataModel >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlNullDataModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlStateMachine >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlStateMachine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlStaticScxmlServiceFactory >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlStaticScxmlServiceFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScxmlTableData >() { return Shiboken::Module::get(SbkPySide6_QtScxmlTypeStructs[SBK_QScxmlTableData_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTSCXML_PYTHON_H

