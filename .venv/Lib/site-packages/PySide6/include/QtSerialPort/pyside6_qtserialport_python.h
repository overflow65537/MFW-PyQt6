// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTSERIALPORT_PYTHON_H
#define SBK_QTSERIALPORT_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtSerialPort/qserialport.h>

QT_BEGIN_NAMESPACE
class QSerialPortInfo;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QSerialPort_Direction_IDX                            = 5,
    SBK_QFlags_QSerialPort_Direction_IDX                     = 0,
    SBK_QSerialPort_BaudRate_IDX                             = 3,
    SBK_QSerialPort_DataBits_IDX                             = 4,
    SBK_QSerialPort_Parity_IDX                               = 7,
    SBK_QSerialPort_StopBits_IDX                             = 10,
    SBK_QSerialPort_FlowControl_IDX                          = 6,
    SBK_QSerialPort_PinoutSignal_IDX                         = 8,
    SBK_QFlags_QSerialPort_PinoutSignal_IDX                  = 1,
    SBK_QSerialPort_SerialPortError_IDX                      = 9,
    SBK_QSerialPort_IDX                                      = 2,
    SBK_QSerialPortInfo_IDX                                  = 11,
    SBK_QtSerialPort_IDX_COUNT                               = 12,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtSerialPortTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtSerialPortModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtSerialPortTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTSERIALPORT_QLIST_INT_IDX                           = 0, // QList<int>
    SBK_QTSERIALPORT_QLIST_QSERIALPORTINFO_IDX               = 1, // QList<QSerialPortInfo>
    SBK_QTSERIALPORT_QLIST_QINT32_IDX                        = 2, // QList<qint32>
    SBK_QTSERIALPORT_QLIST_QVARIANT_IDX                      = 3, // QList<QVariant>
    SBK_QTSERIALPORT_QLIST_QSTRING_IDX                       = 4, // QList<QString>
    SBK_QTSERIALPORT_QMAP_QSTRING_QVARIANT_IDX               = 5, // QMap<QString,QVariant>
    SBK_QTSERIALPORT_CONVERTERS_IDX_COUNT                    = 6,
};

// Converter indices
enum : int {
    SBK_QtSerialPort_QList_int_IDX                           = 0, // QList<int>
    SBK_QtSerialPort_QList_QSerialPortInfo_IDX               = 1, // QList<QSerialPortInfo>
    SBK_QtSerialPort_QList_qint32_IDX                        = 2, // QList<qint32>
    SBK_QtSerialPort_QList_QVariant_IDX                      = 3, // QList<QVariant>
    SBK_QtSerialPort_QList_QString_IDX                       = 4, // QList<QString>
    SBK_QtSerialPort_QMap_QString_QVariant_IDX               = 5, // QMap<QString,QVariant>
    SBK_QtSerialPort_CONVERTERS_IDX_COUNT                    = 6,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QSerialPort::Direction >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QSerialPort::Direction> >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QFlags_QSerialPort_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort::BaudRate >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_BaudRate_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort::DataBits >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_DataBits_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort::Parity >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_Parity_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort::StopBits >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_StopBits_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort::FlowControl >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_FlowControl_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort::PinoutSignal >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_PinoutSignal_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QSerialPort::PinoutSignal> >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QFlags_QSerialPort_PinoutSignal_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort::SerialPortError >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_SerialPortError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPort >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPort_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSerialPortInfo >() { return Shiboken::Module::get(SbkPySide6_QtSerialPortTypeStructs[SBK_QSerialPortInfo_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTSERIALPORT_PYTHON_H

