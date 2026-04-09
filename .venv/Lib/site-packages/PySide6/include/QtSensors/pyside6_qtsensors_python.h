// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTSENSORS_PYTHON_H
#define SBK_QTSENSORS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QtSensors/qaccelerometer.h>
#include <QtSensors/qambientlightsensor.h>
#include <QtSensors/qorientationsensor.h>
#include <QtSensors/qsensor.h>
#include <QtSensors/qtapsensor.h>

QT_BEGIN_NAMESPACE
class QAccelerometerFilter;
class QAccelerometerReading;
class QAmbientLightFilter;
class QAmbientLightSensor;
class QAmbientTemperatureFilter;
class QAmbientTemperatureReading;
class QAmbientTemperatureSensor;
class QCompass;
class QCompassFilter;
class QCompassReading;
class QGyroscope;
class QGyroscopeFilter;
class QGyroscopeReading;
class QHumidityFilter;
class QHumidityReading;
class QHumiditySensor;
class QIRProximityFilter;
class QIRProximityReading;
class QIRProximitySensor;
class QLidFilter;
class QLidReading;
class QLidSensor;
class QLightFilter;
class QLightReading;
class QLightSensor;
class QMagnetometer;
class QMagnetometerFilter;
class QMagnetometerReading;
class QOrientationFilter;
class QOrientationSensor;
class QPressureFilter;
class QPressureReading;
class QPressureSensor;
class QProximityFilter;
class QProximityReading;
class QProximitySensor;
class QRotationFilter;
class QRotationReading;
class QRotationSensor;
class QSensorBackend;
class QSensorBackendFactory;
class QSensorChangesInterface;
class QSensorFilter;
class QSensorManager;
class QSensorPluginInterface;
class QSensorReading;
class QTapFilter;
class QTapSensor;
class QTiltFilter;
class QTiltReading;
class QTiltSensor;
struct qoutputrange;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAccelerometer_AccelerationMode_IDX                  = 1,
    SBK_QAccelerometer_IDX                                   = 0,
    SBK_QAccelerometerFilter_IDX                             = 2,
    SBK_QAccelerometerReading_IDX                            = 3,
    SBK_QAmbientLightFilter_IDX                              = 4,
    SBK_QAmbientLightReading_LightLevel_IDX                  = 6,
    SBK_QAmbientLightReading_IDX                             = 5,
    SBK_QAmbientLightSensor_IDX                              = 7,
    SBK_QAmbientTemperatureFilter_IDX                        = 8,
    SBK_QAmbientTemperatureReading_IDX                       = 9,
    SBK_QAmbientTemperatureSensor_IDX                        = 10,
    SBK_QCompass_IDX                                         = 11,
    SBK_QCompassFilter_IDX                                   = 12,
    SBK_QCompassReading_IDX                                  = 13,
    SBK_QGyroscope_IDX                                       = 14,
    SBK_QGyroscopeFilter_IDX                                 = 15,
    SBK_QGyroscopeReading_IDX                                = 16,
    SBK_QHumidityFilter_IDX                                  = 17,
    SBK_QHumidityReading_IDX                                 = 18,
    SBK_QHumiditySensor_IDX                                  = 19,
    SBK_QIRProximityFilter_IDX                               = 20,
    SBK_QIRProximityReading_IDX                              = 21,
    SBK_QIRProximitySensor_IDX                               = 22,
    SBK_QLidFilter_IDX                                       = 23,
    SBK_QLidReading_IDX                                      = 24,
    SBK_QLidSensor_IDX                                       = 25,
    SBK_QLightFilter_IDX                                     = 26,
    SBK_QLightReading_IDX                                    = 27,
    SBK_QLightSensor_IDX                                     = 28,
    SBK_QMagnetometer_IDX                                    = 29,
    SBK_QMagnetometerFilter_IDX                              = 30,
    SBK_QMagnetometerReading_IDX                             = 31,
    SBK_QOrientationFilter_IDX                               = 32,
    SBK_QOrientationReading_Orientation_IDX                  = 34,
    SBK_QOrientationReading_IDX                              = 33,
    SBK_QOrientationSensor_IDX                               = 35,
    SBK_QPressureFilter_IDX                                  = 36,
    SBK_QPressureReading_IDX                                 = 37,
    SBK_QPressureSensor_IDX                                  = 38,
    SBK_QProximityFilter_IDX                                 = 39,
    SBK_QProximityReading_IDX                                = 40,
    SBK_QProximitySensor_IDX                                 = 41,
    SBK_QRotationFilter_IDX                                  = 42,
    SBK_QRotationReading_IDX                                 = 43,
    SBK_QRotationSensor_IDX                                  = 44,
    SBK_QSensor_Feature_IDX                                  = 47,
    SBK_QSensor_AxesOrientationMode_IDX                      = 46,
    SBK_QSensor_IDX                                          = 45,
    SBK_QSensorBackend_IDX                                   = 48,
    SBK_QSensorBackendFactory_IDX                            = 49,
    SBK_QSensorChangesInterface_IDX                          = 50,
    SBK_QSensorFilter_IDX                                    = 51,
    SBK_QSensorManager_IDX                                   = 52,
    SBK_QSensorPluginInterface_IDX                           = 53,
    SBK_QSensorReading_IDX                                   = 54,
    SBK_QTapFilter_IDX                                       = 55,
    SBK_QTapReading_TapDirection_IDX                         = 57,
    SBK_QTapReading_IDX                                      = 56,
    SBK_QTapSensor_IDX                                       = 58,
    SBK_QTiltFilter_IDX                                      = 59,
    SBK_QTiltReading_IDX                                     = 60,
    SBK_QTiltSensor_IDX                                      = 61,
    SBK_qoutputrange_IDX                                     = 62,
    SBK_QtSensors_IDX_COUNT                                  = 63,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtSensorsTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtSensorsModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtSensorsTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTSENSORS_QLIST_INT_IDX                              = 0, // QList<int>
    SBK_QTSENSORS_STD_PAIR_INT_INT_IDX                       = 1, // std::pair<int,int>
    SBK_QTSENSORS_QLIST_STD_PAIR_INT_INT_IDX                 = 2, // QList<std::pair<int,int>>
    SBK_QTSENSORS_QLIST_QSENSORFILTERPTR_IDX                 = 3, // QList<QSensorFilter*>
    SBK_QTSENSORS_QLIST_QOUTPUTRANGE_IDX                     = 4, // QList<qoutputrange>
    SBK_QTSENSORS_QLIST_QBYTEARRAY_IDX                       = 5, // QList<QByteArray>
    SBK_QTSENSORS_QLIST_QVARIANT_IDX                         = 6, // QList<QVariant>
    SBK_QTSENSORS_QLIST_QSTRING_IDX                          = 7, // QList<QString>
    SBK_QTSENSORS_QMAP_QSTRING_QVARIANT_IDX                  = 8, // QMap<QString,QVariant>
    SBK_QTSENSORS_CONVERTERS_IDX_COUNT                       = 9,
};

// Converter indices
enum : int {
    SBK_QtSensors_QList_int_IDX                              = 0, // QList<int>
    SBK_QtSensors_std_pair_int_int_IDX                       = 1, // std::pair<int,int>
    SBK_QtSensors_QList_std_pair_int_int_IDX                 = 2, // QList<std::pair<int,int>>
    SBK_QtSensors_QList_QSensorFilterPTR_IDX                 = 3, // QList<QSensorFilter*>
    SBK_QtSensors_QList_qoutputrange_IDX                     = 4, // QList<qoutputrange>
    SBK_QtSensors_QList_QByteArray_IDX                       = 5, // QList<QByteArray>
    SBK_QtSensors_QList_QVariant_IDX                         = 6, // QList<QVariant>
    SBK_QtSensors_QList_QString_IDX                          = 7, // QList<QString>
    SBK_QtSensors_QMap_QString_QVariant_IDX                  = 8, // QMap<QString,QVariant>
    SBK_QtSensors_CONVERTERS_IDX_COUNT                       = 9,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAccelerometer::AccelerationMode >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAccelerometer_AccelerationMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAccelerometer >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAccelerometer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAccelerometerFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAccelerometerFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAccelerometerReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAccelerometerReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientLightFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAmbientLightFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientLightReading::LightLevel >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAmbientLightReading_LightLevel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientLightReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAmbientLightReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientLightSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAmbientLightSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientTemperatureFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAmbientTemperatureFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientTemperatureReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAmbientTemperatureReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAmbientTemperatureSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QAmbientTemperatureSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCompass >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QCompass_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCompassFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QCompassFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCompassReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QCompassReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGyroscope >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QGyroscope_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGyroscopeFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QGyroscopeFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGyroscopeReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QGyroscopeReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHumidityFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QHumidityFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHumidityReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QHumidityReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHumiditySensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QHumiditySensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QIRProximityFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QIRProximityFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QIRProximityReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QIRProximityReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QIRProximitySensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QIRProximitySensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLidFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QLidFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLidReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QLidReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLidSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QLidSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLightFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QLightFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLightReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QLightReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLightSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QLightSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMagnetometer >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QMagnetometer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMagnetometerFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QMagnetometerFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMagnetometerReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QMagnetometerReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOrientationFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QOrientationFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOrientationReading::Orientation >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QOrientationReading_Orientation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOrientationReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QOrientationReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOrientationSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QOrientationSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPressureFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QPressureFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPressureReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QPressureReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPressureSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QPressureSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProximityFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QProximityFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProximityReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QProximityReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProximitySensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QProximitySensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRotationFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QRotationFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRotationReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QRotationReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRotationSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QRotationSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensor::Feature >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensor_Feature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensor::AxesOrientationMode >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensor_AxesOrientationMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensorBackend >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensorBackend_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensorBackendFactory >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensorBackendFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensorChangesInterface >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensorChangesInterface_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensorFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensorFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensorManager >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensorManager_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensorPluginInterface >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensorPluginInterface_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSensorReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QSensorReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTapFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QTapFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTapReading::TapDirection >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QTapReading_TapDirection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTapReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QTapReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTapSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QTapSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTiltFilter >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QTiltFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTiltReading >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QTiltReading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTiltSensor >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_QTiltSensor_IDX]); }
template<> inline PyTypeObject *SbkType< ::qoutputrange >() { return Shiboken::Module::get(SbkPySide6_QtSensorsTypeStructs[SBK_qoutputrange_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTSENSORS_PYTHON_H

