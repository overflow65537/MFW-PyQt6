// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QT3DEXTRAS_PYTHON_H
#define SBK_QT3DEXTRAS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qt3drender_python.h>
#include <pyside6_qt3dcore_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>
#include <pyside6_qtopengl_python.h>

// Bound library includes
#include <Qt3DExtras/qabstractcameracontroller.h>

QT_BEGIN_NAMESPACE

namespace Qt3DExtras {
    class QAbstractSpriteSheet;
    class QConeGeometry;
    class QConeGeometryView;
    class QConeMesh;
    class QCuboidGeometry;
    class QCuboidGeometryView;
    class QCuboidMesh;
    class QCylinderGeometry;
    class QCylinderGeometryView;
    class QCylinderMesh;
    class QDiffuseMapMaterial;
    class QDiffuseSpecularMapMaterial;
    class QDiffuseSpecularMaterial;
    class QExtrudedTextGeometry;
    class QExtrudedTextMesh;
    class QFirstPersonCameraController;
    class QForwardRenderer;
    class QGoochMaterial;
    class QMetalRoughMaterial;
    class QMorphPhongMaterial;
    class QNormalDiffuseMapAlphaMaterial;
    class QNormalDiffuseMapMaterial;
    class QNormalDiffuseSpecularMapMaterial;
    class QOrbitCameraController;
    class QPerVertexColorMaterial;
    class QPhongAlphaMaterial;
    class QPhongMaterial;
    class QPlaneGeometry;
    class QPlaneGeometryView;
    class QPlaneMesh;
    class QSkyboxEntity;
    class QSphereGeometry;
    class QSphereGeometryView;
    class QSphereMesh;
    class QSpriteGrid;
    class QSpriteSheet;
    class QSpriteSheetItem;
    class QText2DEntity;
    class QTextureMaterial;
    class QTorusGeometry;
    class QTorusGeometryView;
    class QTorusMesh;
    class Qt3DWindow;
}
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_Qt3DExtrasQt3DExtras_IDX                             = 0,
    SBK_Qt3DExtras_QAbstractCameraController_IDX             = 1,
    SBK_Qt3DExtras_QAbstractCameraController_InputState_IDX  = 2,
    SBK_Qt3DExtras_QAbstractSpriteSheet_IDX                  = 3,
    SBK_Qt3DExtras_QConeGeometry_IDX                         = 4,
    SBK_Qt3DExtras_QConeGeometryView_IDX                     = 5,
    SBK_Qt3DExtras_QConeMesh_IDX                             = 6,
    SBK_Qt3DExtras_QCuboidGeometry_IDX                       = 7,
    SBK_Qt3DExtras_QCuboidGeometryView_IDX                   = 8,
    SBK_Qt3DExtras_QCuboidMesh_IDX                           = 9,
    SBK_Qt3DExtras_QCylinderGeometry_IDX                     = 10,
    SBK_Qt3DExtras_QCylinderGeometryView_IDX                 = 11,
    SBK_Qt3DExtras_QCylinderMesh_IDX                         = 12,
    SBK_Qt3DExtras_QDiffuseMapMaterial_IDX                   = 13,
    SBK_Qt3DExtras_QDiffuseSpecularMapMaterial_IDX           = 14,
    SBK_Qt3DExtras_QDiffuseSpecularMaterial_IDX              = 15,
    SBK_Qt3DExtras_QExtrudedTextGeometry_IDX                 = 16,
    SBK_Qt3DExtras_QExtrudedTextMesh_IDX                     = 17,
    SBK_Qt3DExtras_QFirstPersonCameraController_IDX          = 18,
    SBK_Qt3DExtras_QForwardRenderer_IDX                      = 19,
    SBK_Qt3DExtras_QGoochMaterial_IDX                        = 20,
    SBK_Qt3DExtras_QMetalRoughMaterial_IDX                   = 21,
    SBK_Qt3DExtras_QMorphPhongMaterial_IDX                   = 22,
    SBK_Qt3DExtras_QNormalDiffuseMapAlphaMaterial_IDX        = 23,
    SBK_Qt3DExtras_QNormalDiffuseMapMaterial_IDX             = 24,
    SBK_Qt3DExtras_QNormalDiffuseSpecularMapMaterial_IDX     = 25,
    SBK_Qt3DExtras_QOrbitCameraController_IDX                = 26,
    SBK_Qt3DExtras_QPerVertexColorMaterial_IDX               = 27,
    SBK_Qt3DExtras_QPhongAlphaMaterial_IDX                   = 28,
    SBK_Qt3DExtras_QPhongMaterial_IDX                        = 29,
    SBK_Qt3DExtras_QPlaneGeometry_IDX                        = 30,
    SBK_Qt3DExtras_QPlaneGeometryView_IDX                    = 31,
    SBK_Qt3DExtras_QPlaneMesh_IDX                            = 32,
    SBK_Qt3DExtras_QSkyboxEntity_IDX                         = 33,
    SBK_Qt3DExtras_QSphereGeometry_IDX                       = 34,
    SBK_Qt3DExtras_QSphereGeometryView_IDX                   = 35,
    SBK_Qt3DExtras_QSphereMesh_IDX                           = 36,
    SBK_Qt3DExtras_QSpriteGrid_IDX                           = 37,
    SBK_Qt3DExtras_QSpriteSheet_IDX                          = 38,
    SBK_Qt3DExtras_QSpriteSheetItem_IDX                      = 39,
    SBK_Qt3DExtras_QText2DEntity_IDX                         = 40,
    SBK_Qt3DExtras_QTextureMaterial_IDX                      = 41,
    SBK_Qt3DExtras_QTorusGeometry_IDX                        = 42,
    SBK_Qt3DExtras_QTorusGeometryView_IDX                    = 43,
    SBK_Qt3DExtras_QTorusMesh_IDX                            = 44,
    SBK_Qt3DExtras_Qt3DWindow_IDX                            = 45,
    SBK_Qt3DExtras_IDX_COUNT                                 = 46,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_Qt3DExtrasTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_Qt3DExtrasModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_Qt3DExtrasTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QT3DEXTRAS_QLIST_INT_IDX                             = 0, // QList<int>
    SBK_QT3DEXTRAS_QLIST_QT3DEXTRAS_QSPRITESHEETITEMPTR_IDX  = 1, // QList<Qt3DExtras::QSpriteSheetItem*>
    SBK_QT3DEXTRAS_QLIST_QVARIANT_IDX                        = 2, // QList<QVariant>
    SBK_QT3DEXTRAS_QLIST_QSTRING_IDX                         = 3, // QList<QString>
    SBK_QT3DEXTRAS_QMAP_QSTRING_QVARIANT_IDX                 = 4, // QMap<QString,QVariant>
    SBK_QT3DEXTRAS_CONVERTERS_IDX_COUNT                      = 5,
};

// Converter indices
enum : int {
    SBK_Qt3DExtras_QList_int_IDX                             = 0, // QList<int>
    SBK_Qt3DExtras_QList_Qt3DExtras_QSpriteSheetItemPTR_IDX  = 1, // QList<Qt3DExtras::QSpriteSheetItem*>
    SBK_Qt3DExtras_QList_QVariant_IDX                        = 2, // QList<QVariant>
    SBK_Qt3DExtras_QList_QString_IDX                         = 3, // QList<QString>
    SBK_Qt3DExtras_QMap_QString_QVariant_IDX                 = 4, // QMap<QString,QVariant>
    SBK_Qt3DExtras_CONVERTERS_IDX_COUNT                      = 5,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QAbstractCameraController >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QAbstractCameraController_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QAbstractCameraController::InputState >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QAbstractCameraController_InputState_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QAbstractSpriteSheet >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QAbstractSpriteSheet_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QConeGeometry >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QConeGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QConeGeometryView >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QConeGeometryView_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QConeMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QConeMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QCuboidGeometry >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QCuboidGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QCuboidGeometryView >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QCuboidGeometryView_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QCuboidMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QCuboidMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QCylinderGeometry >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QCylinderGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QCylinderGeometryView >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QCylinderGeometryView_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QCylinderMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QCylinderMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QDiffuseMapMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QDiffuseMapMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QDiffuseSpecularMapMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QDiffuseSpecularMapMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QDiffuseSpecularMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QDiffuseSpecularMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QExtrudedTextGeometry >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QExtrudedTextGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QExtrudedTextMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QExtrudedTextMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QFirstPersonCameraController >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QFirstPersonCameraController_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QForwardRenderer >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QForwardRenderer_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QGoochMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QGoochMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QMetalRoughMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QMetalRoughMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QMorphPhongMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QMorphPhongMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QNormalDiffuseMapAlphaMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QNormalDiffuseMapAlphaMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QNormalDiffuseMapMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QNormalDiffuseMapMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QNormalDiffuseSpecularMapMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QNormalDiffuseSpecularMapMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QOrbitCameraController >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QOrbitCameraController_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QPerVertexColorMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QPerVertexColorMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QPhongAlphaMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QPhongAlphaMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QPhongMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QPhongMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QPlaneGeometry >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QPlaneGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QPlaneGeometryView >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QPlaneGeometryView_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QPlaneMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QPlaneMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QSkyboxEntity >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QSkyboxEntity_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QSphereGeometry >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QSphereGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QSphereGeometryView >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QSphereGeometryView_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QSphereMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QSphereMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QSpriteGrid >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QSpriteGrid_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QSpriteSheet >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QSpriteSheet_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QSpriteSheetItem >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QSpriteSheetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QText2DEntity >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QText2DEntity_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QTextureMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QTextureMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QTorusGeometry >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QTorusGeometry_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QTorusGeometryView >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QTorusGeometryView_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::QTorusMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_QTorusMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DExtras::Qt3DWindow >() { return Shiboken::Module::get(SbkPySide6_Qt3DExtrasTypeStructs[SBK_Qt3DExtras_Qt3DWindow_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QT3DEXTRAS_PYTHON_H

