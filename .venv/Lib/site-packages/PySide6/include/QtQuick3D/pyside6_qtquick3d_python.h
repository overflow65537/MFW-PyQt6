// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTQUICK3D_PYTHON_H
#define SBK_QTQUICK3D_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtquick_python.h>
#include <pyside6_qtcore_python.h>
#include <pyside6_qtnetwork_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtopengl_python.h>
#include <pyside6_qtqml_python.h>

// Bound library includes
#include <QtQuick3D/qquick3dgeometry.h>
#include <QtQuick3D/qquick3dinstancing.h>
#include <QtQuick3D/qquick3dobject.h>
#include <QtQuick3D/qquick3dtexturedata.h>

QT_BEGIN_NAMESPACE
class QQuick3D;
class QQuick3DRenderExtension;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QQuick3D_IDX                                         = 0,
    SBK_QQuick3DGeometry_PrimitiveType_IDX                   = 5,
    SBK_QQuick3DGeometry_IDX                                 = 1,
    SBK_QQuick3DGeometry_Attribute_Semantic_IDX              = 4,
    SBK_QQuick3DGeometry_Attribute_ComponentType_IDX         = 3,
    SBK_QQuick3DGeometry_Attribute_IDX                       = 2,
    SBK_QQuick3DGeometry_TargetAttribute_IDX                 = 6,
    SBK_QQuick3DInstancing_IDX                               = 7,
    SBK_QQuick3DInstancing_InstanceTableEntry_IDX            = 8,
    SBK_QQuick3DObject_ItemChange_IDX                        = 10,
    SBK_QQuick3DObject_IDX                                   = 9,
    SBK_QQuick3DRenderExtension_IDX                          = 11,
    SBK_QQuick3DTextureData_Format_IDX                       = 13,
    SBK_QQuick3DTextureData_IDX                              = 12,
    SBK_QtQuick3D_IDX_COUNT                                  = 14,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtQuick3DTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtQuick3DModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtQuick3DTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTQUICK3D_QLIST_INT_IDX                              = 0, // QList<int>
    SBK_QTQUICK3D_QLIST_QQUICK3DOBJECTPTR_IDX                = 1, // QList<QQuick3DObject*>
    SBK_QTQUICK3D_STD_PAIR_QBYTEARRAY_INT_IDX                = 2, // std::pair<QByteArray,int>
    SBK_QTQUICK3D_QLIST_QVARIANT_IDX                         = 3, // QList<QVariant>
    SBK_QTQUICK3D_QLIST_QSTRING_IDX                          = 4, // QList<QString>
    SBK_QTQUICK3D_QMAP_QSTRING_QVARIANT_IDX                  = 5, // QMap<QString,QVariant>
    SBK_QTQUICK3D_CONVERTERS_IDX_COUNT                       = 6,
};

// Converter indices
enum : int {
    SBK_QtQuick3D_QList_int_IDX                              = 0, // QList<int>
    SBK_QtQuick3D_QList_QQuick3DObjectPTR_IDX                = 1, // QList<QQuick3DObject*>
    SBK_QtQuick3D_std_pair_QByteArray_int_IDX                = 2, // std::pair<QByteArray,int>
    SBK_QtQuick3D_QList_QVariant_IDX                         = 3, // QList<QVariant>
    SBK_QtQuick3D_QList_QString_IDX                          = 4, // QList<QString>
    SBK_QtQuick3D_QMap_QString_QVariant_IDX                  = 5, // QMap<QString,QVariant>
    SBK_QtQuick3D_CONVERTERS_IDX_COUNT                       = 6,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QQuick3D >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3D_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DGeometry::PrimitiveType >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DGeometry_PrimitiveType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DGeometry >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DGeometry::Attribute::Semantic >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DGeometry_Attribute_Semantic_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DGeometry::Attribute::ComponentType >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DGeometry_Attribute_ComponentType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DGeometry::Attribute >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DGeometry_Attribute_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DGeometry::TargetAttribute >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DGeometry_TargetAttribute_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DInstancing >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DInstancing_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DInstancing::InstanceTableEntry >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DInstancing_InstanceTableEntry_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DObject::ItemChange >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DObject_ItemChange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DObject >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DObject_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DRenderExtension >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DRenderExtension_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DTextureData::Format >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DTextureData_Format_IDX]); }
template<> inline PyTypeObject *SbkType< ::QQuick3DTextureData >() { return Shiboken::Module::get(SbkPySide6_QtQuick3DTypeStructs[SBK_QQuick3DTextureData_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTQUICK3D_PYTHON_H

