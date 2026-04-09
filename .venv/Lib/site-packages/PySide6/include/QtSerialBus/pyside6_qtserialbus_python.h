// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTSERIALBUS_PYTHON_H
#define SBK_QTSERIALBUS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtnetwork_python.h>
#include <pyside6_qtserialport_python.h>

// Bound library includes
#include <QtSerialBus/qcanbusdevice.h>
#include <QtSerialBus/qcanbusframe.h>
#include <QtSerialBus/qcancommondefinitions.h>
#include <QtSerialBus/qcandbcfileparser.h>
#include <QtSerialBus/qcanframeprocessor.h>
#include <QtSerialBus/qcansignaldescription.h>
#include <QtSerialBus/qmodbusdataunit.h>
#include <QtSerialBus/qmodbusdevice.h>
#include <QtSerialBus/qmodbusdeviceidentification.h>
#include <QtSerialBus/qmodbuspdu.h>
#include <QtSerialBus/qmodbusreply.h>
#include <QtSerialBus/qmodbusserver.h>

QT_BEGIN_NAMESPACE
class QCanBus;
class QCanBusDeviceInfo;
class QCanBusFactory;
class QCanMessageDescription;
class QCanUniqueIdDescription;
class QModbusClient;
class QModbusExceptionResponse;
class QModbusRequest;
class QModbusResponse;
class QModbusRtuSerialClient;
class QModbusRtuSerialServer;
class QModbusTcpClient;
class QModbusTcpConnectionObserver;
class QModbusTcpServer;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QCanBus_IDX                                          = 0,
    SBK_QCanBusDevice_CanBusError_IDX                        = 3,
    SBK_QCanBusDevice_CanBusDeviceState_IDX                  = 2,
    SBK_QCanBusDevice_CanBusStatus_IDX                       = 4,
    SBK_QCanBusDevice_ConfigurationKey_IDX                   = 5,
    SBK_QCanBusDevice_Direction_IDX                          = 6,
    SBK_QFlags_QCanBusDevice_Direction_IDX                   = 24,
    SBK_QCanBusDevice_IDX                                    = 1,
    SBK_QCanBusDevice_Filter_FormatFilter_IDX                = 8,
    SBK_QFlags_QCanBusDevice_Filter_FormatFilter_IDX         = 25,
    SBK_QCanBusDevice_Filter_IDX                             = 7,
    SBK_QCanBusDeviceInfo_IDX                                = 9,
    SBK_QCanBusFactory_IDX                                   = 10,
    SBK_QCanBusFrame_FrameType_IDX                           = 13,
    SBK_QCanBusFrame_FrameError_IDX                          = 12,
    SBK_QFlags_QCanBusFrame_FrameError_IDX                   = 26,
    SBK_QCanBusFrame_IDX                                     = 11,
    SBK_QCanBusFrame_TimeStamp_IDX                           = 14,
    SBK_QCanDbcFileParser_Error_IDX                          = 16,
    SBK_QCanDbcFileParser_IDX                                = 15,
    SBK_QCanFrameProcessor_Error_IDX                         = 18,
    SBK_QCanFrameProcessor_IDX                               = 17,
    SBK_QCanFrameProcessor_ParseResult_IDX                   = 19,
    SBK_QCanMessageDescription_IDX                           = 20,
    SBK_QCanSignalDescription_IDX                            = 21,
    SBK_QCanSignalDescription_MultiplexValueRange_IDX        = 22,
    SBK_QCanUniqueIdDescription_IDX                          = 23,
    SBK_QModbusClient_IDX                                    = 27,
    SBK_QModbusDataUnit_RegisterType_IDX                     = 29,
    SBK_QModbusDataUnit_IDX                                  = 28,
    SBK_QModbusDevice_Error_IDX                              = 32,
    SBK_QModbusDevice_State_IDX                              = 34,
    SBK_QModbusDevice_ConnectionParameter_IDX                = 31,
    SBK_QModbusDevice_IntermediateError_IDX                  = 33,
    SBK_QModbusDevice_IDX                                    = 30,
    SBK_QModbusDeviceIdentification_ObjectId_IDX             = 37,
    SBK_QModbusDeviceIdentification_ReadDeviceIdCode_IDX     = 38,
    SBK_QModbusDeviceIdentification_ConformityLevel_IDX      = 36,
    SBK_QModbusDeviceIdentification_IDX                      = 35,
    SBK_QModbusExceptionResponse_IDX                         = 39,
    SBK_QModbusPdu_ExceptionCode_IDX                         = 41,
    SBK_QModbusPdu_FunctionCode_IDX                          = 42,
    SBK_QModbusPdu_IDX                                       = 40,
    SBK_QModbusReply_ReplyType_IDX                           = 44,
    SBK_QModbusReply_IDX                                     = 43,
    SBK_QModbusRequest_IDX                                   = 45,
    SBK_QModbusResponse_IDX                                  = 46,
    SBK_QModbusRtuSerialClient_IDX                           = 47,
    SBK_QModbusRtuSerialServer_IDX                           = 48,
    SBK_QModbusServer_Option_IDX                             = 50,
    SBK_QModbusServer_IDX                                    = 49,
    SBK_QModbusTcpClient_IDX                                 = 51,
    SBK_QModbusTcpConnectionObserver_IDX                     = 52,
    SBK_QModbusTcpServer_IDX                                 = 53,
    SBK_QtCanBus_DataSource_IDX                              = 56,
    SBK_QtCanBus_DataFormat_IDX                              = 55,
    SBK_QtCanBus_MultiplexState_IDX                          = 57,
    SBK_QtCanBus_UniqueId_IDX                                = 58,
    SBK_QtSerialBusQtCanBus_IDX                              = 54,
    SBK_QtSerialBus_IDX_COUNT                                = 59,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtSerialBusTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtSerialBusModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtSerialBusTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTSERIALBUS_QLIST_INT_IDX                            = 0, // QList<int>
    SBK_QTSERIALBUS_QLIST_QUINT16_IDX                        = 1, // QList<quint16>
    SBK_QTSERIALBUS_QLIST_QCANSIGNALDESCRIPTION_MULTIPLEXVALUERANGE_IDX = 2, // QList<QCanSignalDescription::MultiplexValueRange>
    SBK_QTSERIALBUS_QHASH_QSTRING_QLIST_QCANSIGNALDESCRIPTION_MULTIPLEXVALUERANGE_IDX = 3, // QHash<QString,QList<QCanSignalDescription::MultiplexValueRange>>
    SBK_QTSERIALBUS_QLIST_QCANSIGNALDESCRIPTION_IDX          = 4, // QList<QCanSignalDescription>
    SBK_QTSERIALBUS_QLIST_QCANMESSAGEDESCRIPTION_IDX         = 5, // QList<QCanMessageDescription>
    SBK_QTSERIALBUS_QMAP_QSTRING_QVARIANT_IDX                = 6, // QMap<QString,QVariant>
    SBK_QTSERIALBUS_QHASH_UNSIGNEDINT_QSTRING_IDX            = 7, // QHash<unsigned int,QString>
    SBK_QTSERIALBUS_QHASH_QSTRING_QHASH_UNSIGNEDINT_QSTRING_IDX = 8, // QHash<QString,QHash<unsigned int,QString>>
    SBK_QTSERIALBUS_QHASH_QTCANBUS_UNIQUEID_QHASH_QSTRING_QHASH_UNSIGNEDINT_QSTRING_IDX = 9, // QHash<QtCanBus::UniqueId,QHash<QString,QHash<unsigned int,QString>>>
    SBK_QTSERIALBUS_QLIST_QCANBUSDEVICEINFO_IDX              = 10, // QList<QCanBusDeviceInfo>
    SBK_QTSERIALBUS_QLIST_QMODBUSDEVICE_INTERMEDIATEERROR_IDX = 11, // QList<QModbusDevice::IntermediateError>
    SBK_QTSERIALBUS_QMAP_QMODBUSDATAUNIT_REGISTERTYPE_QMODBUSDATAUNIT_IDX = 12, // QMap<QModbusDataUnit::RegisterType,QModbusDataUnit>
    SBK_QTSERIALBUS_QLIST_QCANBUSDEVICE_CONFIGURATIONKEY_IDX = 13, // QList<QCanBusDevice::ConfigurationKey>
    SBK_QTSERIALBUS_QLIST_QCANBUSFRAME_IDX                   = 14, // QList<QCanBusFrame>
    SBK_QTSERIALBUS_QLIST_QVARIANT_IDX                       = 15, // QList<QVariant>
    SBK_QTSERIALBUS_QLIST_QSTRING_IDX                        = 16, // QList<QString>
    SBK_QTSERIALBUS_CONVERTERS_IDX_COUNT                     = 17,
};

// Converter indices
enum : int {
    SBK_QtSerialBus_QList_int_IDX                            = 0, // QList<int>
    SBK_QtSerialBus_QList_quint16_IDX                        = 1, // QList<quint16>
    SBK_QtSerialBus_QList_QCanSignalDescription_MultiplexValueRange_IDX = 2, // QList<QCanSignalDescription::MultiplexValueRange>
    SBK_QtSerialBus_QHash_QString_QList_QCanSignalDescription_MultiplexValueRange_IDX = 3, // QHash<QString,QList<QCanSignalDescription::MultiplexValueRange>>
    SBK_QtSerialBus_QList_QCanSignalDescription_IDX          = 4, // QList<QCanSignalDescription>
    SBK_QtSerialBus_QList_QCanMessageDescription_IDX         = 5, // QList<QCanMessageDescription>
    SBK_QtSerialBus_QMap_QString_QVariant_IDX                = 6, // QMap<QString,QVariant>
    SBK_QtSerialBus_QHash_unsignedint_QString_IDX            = 7, // QHash<unsigned int,QString>
    SBK_QtSerialBus_QHash_QString_QHash_unsignedint_QString_IDX = 8, // QHash<QString,QHash<unsigned int,QString>>
    SBK_QtSerialBus_QHash_QtCanBus_UniqueId_QHash_QString_QHash_unsignedint_QString_IDX = 9, // QHash<QtCanBus::UniqueId,QHash<QString,QHash<unsigned int,QString>>>
    SBK_QtSerialBus_QList_QCanBusDeviceInfo_IDX              = 10, // QList<QCanBusDeviceInfo>
    SBK_QtSerialBus_QList_QModbusDevice_IntermediateError_IDX = 11, // QList<QModbusDevice::IntermediateError>
    SBK_QtSerialBus_QMap_QModbusDataUnit_RegisterType_QModbusDataUnit_IDX = 12, // QMap<QModbusDataUnit::RegisterType,QModbusDataUnit>
    SBK_QtSerialBus_QList_QCanBusDevice_ConfigurationKey_IDX = 13, // QList<QCanBusDevice::ConfigurationKey>
    SBK_QtSerialBus_QList_QCanBusFrame_IDX                   = 14, // QList<QCanBusFrame>
    SBK_QtSerialBus_QList_QVariant_IDX                       = 15, // QList<QVariant>
    SBK_QtSerialBus_QList_QString_IDX                        = 16, // QList<QString>
    SBK_QtSerialBus_CONVERTERS_IDX_COUNT                     = 17,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QCanBus >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBus_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice::CanBusError >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_CanBusError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice::CanBusDeviceState >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_CanBusDeviceState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice::CanBusStatus >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_CanBusStatus_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice::ConfigurationKey >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_ConfigurationKey_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice::Direction >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanBusDevice::Direction> >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QFlags_QCanBusDevice_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice::Filter::FormatFilter >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_Filter_FormatFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanBusDevice::Filter::FormatFilter> >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QFlags_QCanBusDevice_Filter_FormatFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDevice::Filter >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDevice_Filter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusDeviceInfo >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusDeviceInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusFactory >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusFrame::FrameType >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusFrame_FrameType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusFrame::FrameError >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusFrame_FrameError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanBusFrame::FrameError> >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QFlags_QCanBusFrame_FrameError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusFrame >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusFrame_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanBusFrame::TimeStamp >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanBusFrame_TimeStamp_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanDbcFileParser::Error >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanDbcFileParser_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanDbcFileParser >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanDbcFileParser_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanFrameProcessor::Error >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanFrameProcessor_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanFrameProcessor >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanFrameProcessor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanFrameProcessor::ParseResult >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanFrameProcessor_ParseResult_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanMessageDescription >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanMessageDescription_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanSignalDescription >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanSignalDescription_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanSignalDescription::MultiplexValueRange >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanSignalDescription_MultiplexValueRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanUniqueIdDescription >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QCanUniqueIdDescription_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusClient >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusClient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDataUnit::RegisterType >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDataUnit_RegisterType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDataUnit >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDataUnit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDevice::Error >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDevice_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDevice::State >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDevice_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDevice::ConnectionParameter >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDevice_ConnectionParameter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDevice::IntermediateError >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDevice_IntermediateError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDevice >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDeviceIdentification::ObjectId >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDeviceIdentification_ObjectId_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDeviceIdentification::ReadDeviceIdCode >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDeviceIdentification_ReadDeviceIdCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDeviceIdentification::ConformityLevel >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDeviceIdentification_ConformityLevel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusDeviceIdentification >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusDeviceIdentification_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusExceptionResponse >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusExceptionResponse_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusPdu::ExceptionCode >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusPdu_ExceptionCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusPdu::FunctionCode >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusPdu_FunctionCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusPdu >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusPdu_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusReply::ReplyType >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusReply_ReplyType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusReply >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusRequest >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusRequest_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusResponse >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusResponse_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusRtuSerialClient >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusRtuSerialClient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusRtuSerialServer >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusRtuSerialServer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusServer::Option >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusServer_Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusServer >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusServer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusTcpClient >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusTcpClient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusTcpConnectionObserver >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusTcpConnectionObserver_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModbusTcpServer >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QModbusTcpServer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCanBus::DataSource >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QtCanBus_DataSource_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCanBus::DataFormat >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QtCanBus_DataFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCanBus::MultiplexState >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QtCanBus_MultiplexState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCanBus::UniqueId >() { return Shiboken::Module::get(SbkPySide6_QtSerialBusTypeStructs[SBK_QtCanBus_UniqueId_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTSERIALBUS_PYTHON_H

