// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTGRAPHS_PYTHON_H
#define SBK_QTGRAPHS_PYTHON_H

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
#include <QtGraphs/qabstract3daxis.h>
#include <QtGraphs/qabstract3dseries.h>
#include <QtGraphs/qabstractaxis.h>
#include <QtGraphs/qabstractdataproxy.h>
#include <QtGraphs/qabstractseries.h>
#include <QtGraphs/qbarcategoryaxis.h>
#include <QtGraphs/qbardataproxy.h>
#include <QtGraphs/qbarseries.h>
#include <QtGraphs/qgraphs3dnamespace.h>
#include <QtGraphs/qgraphstheme.h>
#include <QtGraphs/qitemmodelbardataproxy.h>
#include <QtGraphs/qitemmodelsurfacedataproxy.h>
#include <QtGraphs/qlineseries.h>
#include <QtGraphs/qpieseries.h>
#include <QtGraphs/qpieslice.h>
#include <QtGraphs/qsurface3dseries.h>

QT_BEGIN_NAMESPACE
class Q3DScene;
class QAreaSeries;
class QBar3DSeries;
class QBarDataItem;
class QBarModelMapper;
class QBarSet;
class QCategory3DAxis;
class QCustom3DItem;
class QCustom3DLabel;
class QCustom3DVolume;
class QCustomSeries;
class QDateTimeAxis;
class QGraphsLine;
struct QGraphsThemeDirtyBitField;
class QHeightMapSurfaceDataProxy;
class QItemModelScatterDataProxy;
struct QLegendData;
class QLogValue3DAxisFormatter;
class QPieModelMapper;
class QScatter3DSeries;
class QScatterDataItem;
class QScatterDataProxy;
class QScatterSeries;
class QSpline3DSeries;
class QSplineSeries;
class QSurfaceDataItem;
class QSurfaceDataProxy;
class QValue3DAxis;
class QValue3DAxisFormatter;
class QValueAxis;
class QXYModelMapper;
class QXYSeries;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_Q3DScene_IDX                                         = 0,
    SBK_QAbstract3DAxis_AxisOrientation_IDX                  = 2,
    SBK_QAbstract3DAxis_AxisType_IDX                         = 3,
    SBK_QAbstract3DAxis_IDX                                  = 1,
    SBK_QAbstract3DSeries_SeriesType_IDX                     = 7,
    SBK_QAbstract3DSeries_Mesh_IDX                           = 6,
    SBK_QAbstract3DSeries_LightingMode_IDX                   = 5,
    SBK_QAbstract3DSeries_IDX                                = 4,
    SBK_QAbstractAxis_AxisType_IDX                           = 9,
    SBK_QAbstractAxis_IDX                                    = 8,
    SBK_QAbstractDataProxy_DataType_IDX                      = 11,
    SBK_QAbstractDataProxy_IDX                               = 10,
    SBK_QAbstractSeries_SeriesType_IDX                       = 13,
    SBK_QAbstractSeries_IDX                                  = 12,
    SBK_QAreaSeries_IDX                                      = 14,
    SBK_QBar3DSeries_IDX                                     = 15,
    SBK_QBarCategoryAxis_LabelPosition_IDX                   = 17,
    SBK_QBarCategoryAxis_IDX                                 = 16,
    SBK_QBarDataItem_IDX                                     = 18,
    SBK_QBarDataProxy_RemoveLabels_IDX                       = 20,
    SBK_QBarDataProxy_IDX                                    = 19,
    SBK_QBarModelMapper_IDX                                  = 21,
    SBK_QBarSeries_LabelsPosition_IDX                        = 24,
    SBK_QBarSeries_BarsType_IDX                              = 23,
    SBK_QBarSeries_IDX                                       = 22,
    SBK_QBarSet_IDX                                          = 25,
    SBK_QCategory3DAxis_IDX                                  = 26,
    SBK_QCustom3DItem_IDX                                    = 27,
    SBK_QCustom3DLabel_IDX                                   = 28,
    SBK_QCustom3DVolume_IDX                                  = 29,
    SBK_QCustomSeries_IDX                                    = 30,
    SBK_QDateTimeAxis_IDX                                    = 31,
    SBK_QGraphsLine_IDX                                      = 35,
    SBK_QGraphsTheme_Theme_IDX                               = 40,
    SBK_QGraphsTheme_ColorStyle_IDX                          = 38,
    SBK_QGraphsTheme_ForceTheme_IDX                          = 39,
    SBK_QGraphsTheme_ColorScheme_IDX                         = 37,
    SBK_QGraphsTheme_IDX                                     = 36,
    SBK_QGraphsThemeDirtyBitField_IDX                        = 41,
    SBK_QHeightMapSurfaceDataProxy_IDX                       = 42,
    SBK_QItemModelBarDataProxy_MultiMatchBehavior_IDX        = 44,
    SBK_QItemModelBarDataProxy_IDX                           = 43,
    SBK_QItemModelScatterDataProxy_IDX                       = 45,
    SBK_QItemModelSurfaceDataProxy_MultiMatchBehavior_IDX    = 47,
    SBK_QItemModelSurfaceDataProxy_IDX                       = 46,
    SBK_QLegendData_IDX                                      = 48,
    SBK_QLineSeries_LineStyle_IDX                            = 50,
    SBK_QLineSeries_StrokeStyle_IDX                          = 51,
    SBK_QLineSeries_IDX                                      = 49,
    SBK_QLogValue3DAxisFormatter_IDX                         = 52,
    SBK_QPieModelMapper_IDX                                  = 53,
    SBK_QPieSeries_LabelVisibility_IDX                       = 55,
    SBK_QPieSeries_IDX                                       = 54,
    SBK_QPieSlice_LabelPosition_IDX                          = 57,
    SBK_QPieSlice_IDX                                        = 56,
    SBK_QScatter3DSeries_IDX                                 = 58,
    SBK_QScatterDataItem_IDX                                 = 59,
    SBK_QScatterDataProxy_IDX                                = 60,
    SBK_QScatterSeries_IDX                                   = 61,
    SBK_QSpline3DSeries_IDX                                  = 62,
    SBK_QSplineSeries_IDX                                    = 63,
    SBK_QSurface3DSeries_DrawFlag_IDX                        = 65,
    SBK_QFlags_QSurface3DSeries_DrawFlag_IDX                 = 32,
    SBK_QSurface3DSeries_Shading_IDX                         = 66,
    SBK_QSurface3DSeries_IDX                                 = 64,
    SBK_QSurfaceDataItem_IDX                                 = 67,
    SBK_QSurfaceDataProxy_IDX                                = 68,
    SBK_QValue3DAxis_IDX                                     = 69,
    SBK_QValue3DAxisFormatter_IDX                            = 70,
    SBK_QValueAxis_IDX                                       = 71,
    SBK_QXYModelMapper_IDX                                   = 72,
    SBK_QXYSeries_IDX                                        = 73,
    SBK_QtGraphs3D_SelectionFlag_IDX                         = 80,
    SBK_QFlags_QtGraphs3D_SelectionFlag_IDX                  = 34,
    SBK_QtGraphs3D_SliceCaptureType_IDX                      = 82,
    SBK_QtGraphs3D_ShadowQuality_IDX                         = 81,
    SBK_QtGraphs3D_ElementType_IDX                           = 76,
    SBK_QtGraphs3D_OptimizationHint_IDX                      = 78,
    SBK_QFlags_QtGraphs3D_OptimizationHint_IDX               = 33,
    SBK_QtGraphs3D_RenderingMode_IDX                         = 79,
    SBK_QtGraphs3D_CameraPreset_IDX                          = 75,
    SBK_QtGraphs3D_GridLineType_IDX                          = 77,
    SBK_QtGraphs3D_TransparencyTechnique_IDX                 = 83,
    SBK_QtGraphsQtGraphs3D_IDX                               = 74,
    SBK_QtGraphs_IDX_COUNT                                   = 84,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtGraphsTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtGraphsModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtGraphsTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTGRAPHS_QLIST_INT_IDX                               = 0, // QList<int>
    SBK_QTGRAPHS_QLIST_FLOAT_IDX                             = 1, // QList<float>
    SBK_QTGRAPHS_QLIST_QPIESLICEPTR_IDX                      = 2, // QList<QPieSlice*>
    SBK_QTGRAPHS_QLIST_QCOLOR_IDX                            = 3, // QList<QColor>
    SBK_QTGRAPHS_QLIST_QLINEARGRADIENT_IDX                   = 4, // QList<QLinearGradient>
    SBK_QTGRAPHS_QLIST_UCHAR_IDX                             = 5, // QList<uchar>
    SBK_QTGRAPHS_QLIST_UNSIGNEDINT_IDX                       = 6, // QList<unsigned int>
    SBK_QTGRAPHS_QLIST_QIMAGEPTR_IDX                         = 7, // QList<QImage*>
    SBK_QTGRAPHS_QLIST_QREAL_IDX                             = 8, // QList<qreal>
    SBK_QTGRAPHS_QLIST_QSIZETYPE_IDX                         = 9, // QList<qsizetype>
    SBK_QTGRAPHS_QLIST_QVARIANT_IDX                          = 10, // QList<QVariant>
    SBK_QTGRAPHS_QLIST_QLEGENDDATA_IDX                       = 11, // QList<QLegendData>
    SBK_QTGRAPHS_QLIST_QPOINTF_IDX                           = 12, // QList<QPointF>
    SBK_QTGRAPHS_QMAP_QSTRING_QVARIANT_IDX                   = 13, // QMap<QString,QVariant>
    SBK_QTGRAPHS_QLIST_QBARSETPTR_IDX                        = 14, // QList<QBarSet*>
    SBK_QTGRAPHS_QLIST_QSURFACEDATAITEM_IDX                  = 15, // QList<QSurfaceDataItem>
    SBK_QTGRAPHS_QLIST_QLIST_QSURFACEDATAITEM_IDX            = 16, // QList<QList<QSurfaceDataItem>>
    SBK_QTGRAPHS_QLIST_QSCATTERDATAITEM_IDX                  = 17, // QList<QScatterDataItem>
    SBK_QTGRAPHS_QLIST_QVECTOR3D_IDX                         = 18, // QList<QVector3D>
    SBK_QTGRAPHS_QLIST_QBARDATAITEM_IDX                      = 19, // QList<QBarDataItem>
    SBK_QTGRAPHS_QLIST_QLIST_QBARDATAITEM_IDX                = 20, // QList<QList<QBarDataItem>>
    SBK_QTGRAPHS_QLIST_QSTRING_IDX                           = 21, // QList<QString>
    SBK_QTGRAPHS_CONVERTERS_IDX_COUNT                        = 22,
};

// Converter indices
enum : int {
    SBK_QtGraphs_QList_int_IDX                               = 0, // QList<int>
    SBK_QtGraphs_QList_float_IDX                             = 1, // QList<float>
    SBK_QtGraphs_QList_QPieSlicePTR_IDX                      = 2, // QList<QPieSlice*>
    SBK_QtGraphs_QList_QColor_IDX                            = 3, // QList<QColor>
    SBK_QtGraphs_QList_QLinearGradient_IDX                   = 4, // QList<QLinearGradient>
    SBK_QtGraphs_QList_uchar_IDX                             = 5, // QList<uchar>
    SBK_QtGraphs_QList_unsignedint_IDX                       = 6, // QList<unsigned int>
    SBK_QtGraphs_QList_QImagePTR_IDX                         = 7, // QList<QImage*>
    SBK_QtGraphs_QList_qreal_IDX                             = 8, // QList<qreal>
    SBK_QtGraphs_QList_qsizetype_IDX                         = 9, // QList<qsizetype>
    SBK_QtGraphs_QList_QVariant_IDX                          = 10, // QList<QVariant>
    SBK_QtGraphs_QList_QLegendData_IDX                       = 11, // QList<QLegendData>
    SBK_QtGraphs_QList_QPointF_IDX                           = 12, // QList<QPointF>
    SBK_QtGraphs_QMap_QString_QVariant_IDX                   = 13, // QMap<QString,QVariant>
    SBK_QtGraphs_QList_QBarSetPTR_IDX                        = 14, // QList<QBarSet*>
    SBK_QtGraphs_QList_QSurfaceDataItem_IDX                  = 15, // QList<QSurfaceDataItem>
    SBK_QtGraphs_QList_QList_QSurfaceDataItem_IDX            = 16, // QList<QList<QSurfaceDataItem>>
    SBK_QtGraphs_QList_QScatterDataItem_IDX                  = 17, // QList<QScatterDataItem>
    SBK_QtGraphs_QList_QVector3D_IDX                         = 18, // QList<QVector3D>
    SBK_QtGraphs_QList_QBarDataItem_IDX                      = 19, // QList<QBarDataItem>
    SBK_QtGraphs_QList_QList_QBarDataItem_IDX                = 20, // QList<QList<QBarDataItem>>
    SBK_QtGraphs_QList_QString_IDX                           = 21, // QList<QString>
    SBK_QtGraphs_CONVERTERS_IDX_COUNT                        = 22,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::Q3DScene >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_Q3DScene_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstract3DAxis::AxisOrientation >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstract3DAxis_AxisOrientation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstract3DAxis::AxisType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstract3DAxis_AxisType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstract3DAxis >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstract3DAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstract3DSeries::SeriesType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstract3DSeries_SeriesType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstract3DSeries::Mesh >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstract3DSeries_Mesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstract3DSeries::LightingMode >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstract3DSeries_LightingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstract3DSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstract3DSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractAxis::AxisType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstractAxis_AxisType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractAxis >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstractAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractDataProxy::DataType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstractDataProxy_DataType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstractDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSeries::SeriesType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstractSeries_SeriesType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAbstractSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAreaSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QAreaSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBar3DSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBar3DSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarCategoryAxis::LabelPosition >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarCategoryAxis_LabelPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarCategoryAxis >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarCategoryAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarDataItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarDataItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarDataProxy::RemoveLabels >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarDataProxy_RemoveLabels_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarModelMapper >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarModelMapper_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarSeries::LabelsPosition >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarSeries_LabelsPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarSeries::BarsType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarSeries_BarsType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBarSet >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QBarSet_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCategory3DAxis >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QCategory3DAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCustom3DItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QCustom3DItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCustom3DLabel >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QCustom3DLabel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCustom3DVolume >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QCustom3DVolume_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCustomSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QCustomSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDateTimeAxis >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QDateTimeAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphsLine >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QGraphsLine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphsTheme::Theme >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QGraphsTheme_Theme_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphsTheme::ColorStyle >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QGraphsTheme_ColorStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphsTheme::ForceTheme >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QGraphsTheme_ForceTheme_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphsTheme::ColorScheme >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QGraphsTheme_ColorScheme_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphsTheme >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QGraphsTheme_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphsThemeDirtyBitField >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QGraphsThemeDirtyBitField_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHeightMapSurfaceDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QHeightMapSurfaceDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemModelBarDataProxy::MultiMatchBehavior >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QItemModelBarDataProxy_MultiMatchBehavior_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemModelBarDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QItemModelBarDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemModelScatterDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QItemModelScatterDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemModelSurfaceDataProxy::MultiMatchBehavior >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QItemModelSurfaceDataProxy_MultiMatchBehavior_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemModelSurfaceDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QItemModelSurfaceDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLegendData >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QLegendData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineSeries::LineStyle >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QLineSeries_LineStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineSeries::StrokeStyle >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QLineSeries_StrokeStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QLineSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLogValue3DAxisFormatter >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QLogValue3DAxisFormatter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPieModelMapper >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QPieModelMapper_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPieSeries::LabelVisibility >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QPieSeries_LabelVisibility_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPieSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QPieSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPieSlice::LabelPosition >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QPieSlice_LabelPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPieSlice >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QPieSlice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScatter3DSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QScatter3DSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScatterDataItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QScatterDataItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScatterDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QScatterDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScatterSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QScatterSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSpline3DSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QSpline3DSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSplineSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QSplineSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSurface3DSeries::DrawFlag >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QSurface3DSeries_DrawFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QSurface3DSeries::DrawFlag> >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QFlags_QSurface3DSeries_DrawFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSurface3DSeries::Shading >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QSurface3DSeries_Shading_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSurface3DSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QSurface3DSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSurfaceDataItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QSurfaceDataItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSurfaceDataProxy >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QSurfaceDataProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QValue3DAxis >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QValue3DAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QValue3DAxisFormatter >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QValue3DAxisFormatter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QValueAxis >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QValueAxis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXYModelMapper >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QXYModelMapper_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXYSeries >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QXYSeries_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::SelectionFlag >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_SelectionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QtGraphs3D::SelectionFlag> >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QFlags_QtGraphs3D_SelectionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::SliceCaptureType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_SliceCaptureType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::ShadowQuality >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_ShadowQuality_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::ElementType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_ElementType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::OptimizationHint >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_OptimizationHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QtGraphs3D::OptimizationHint> >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QFlags_QtGraphs3D_OptimizationHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::RenderingMode >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_RenderingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::CameraPreset >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_CameraPreset_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::GridLineType >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_GridLineType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtGraphs3D::TransparencyTechnique >() { return Shiboken::Module::get(SbkPySide6_QtGraphsTypeStructs[SBK_QtGraphs3D_TransparencyTechnique_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTGRAPHS_PYTHON_H

