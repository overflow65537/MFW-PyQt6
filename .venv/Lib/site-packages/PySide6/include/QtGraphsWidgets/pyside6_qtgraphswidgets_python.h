// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTGRAPHSWIDGETS_PYTHON_H
#define SBK_QTGRAPHSWIDGETS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtquickwidgets_python.h>
#include <pyside6_qtcore_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtquick_python.h>
#include <pyside6_qtnetwork_python.h>
#include <pyside6_qtopengl_python.h>
#include <pyside6_qtqml_python.h>
#include <pyside6_qtwidgets_python.h>
#include <pyside6_qtgraphs_python.h>

// Bound library includes

QT_BEGIN_NAMESPACE
class Q3DBarsWidgetItem;
class Q3DGraphsWidgetItem;
class Q3DScatterWidgetItem;
class Q3DSurfaceWidgetItem;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_Q3DBarsWidgetItem_IDX                                = 0,
    SBK_Q3DGraphsWidgetItem_IDX                              = 1,
    SBK_Q3DScatterWidgetItem_IDX                             = 2,
    SBK_Q3DSurfaceWidgetItem_IDX                             = 3,
    SBK_QtGraphsWidgets_IDX_COUNT                            = 4,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtGraphsWidgetsTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtGraphsWidgetsModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtGraphsWidgetsTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTGRAPHSWIDGETS_QLIST_INT_IDX                        = 0, // QList<int>
    SBK_QTGRAPHSWIDGETS_QLIST_QCUSTOM3DITEMPTR_IDX           = 1, // QList<QCustom3DItem*>
    SBK_QTGRAPHSWIDGETS_QLIST_QGRAPHSTHEMEPTR_IDX            = 2, // QList<QGraphsTheme*>
    SBK_QTGRAPHSWIDGETS_QLIST_QVALUE3DAXISPTR_IDX            = 3, // QList<QValue3DAxis*>
    SBK_QTGRAPHSWIDGETS_QLIST_QSURFACE3DSERIESPTR_IDX        = 4, // QList<QSurface3DSeries*>
    SBK_QTGRAPHSWIDGETS_QLIST_QSCATTER3DSERIESPTR_IDX        = 5, // QList<QScatter3DSeries*>
    SBK_QTGRAPHSWIDGETS_QLIST_QABSTRACT3DAXISPTR_IDX         = 6, // QList<QAbstract3DAxis*>
    SBK_QTGRAPHSWIDGETS_QLIST_QBAR3DSERIESPTR_IDX            = 7, // QList<QBar3DSeries*>
    SBK_QTGRAPHSWIDGETS_QLIST_QVARIANT_IDX                   = 8, // QList<QVariant>
    SBK_QTGRAPHSWIDGETS_QLIST_QSTRING_IDX                    = 9, // QList<QString>
    SBK_QTGRAPHSWIDGETS_QMAP_QSTRING_QVARIANT_IDX            = 10, // QMap<QString,QVariant>
    SBK_QTGRAPHSWIDGETS_CONVERTERS_IDX_COUNT                 = 11,
};

// Converter indices
enum : int {
    SBK_QtGraphsWidgets_QList_int_IDX                        = 0, // QList<int>
    SBK_QtGraphsWidgets_QList_QCustom3DItemPTR_IDX           = 1, // QList<QCustom3DItem*>
    SBK_QtGraphsWidgets_QList_QGraphsThemePTR_IDX            = 2, // QList<QGraphsTheme*>
    SBK_QtGraphsWidgets_QList_QValue3DAxisPTR_IDX            = 3, // QList<QValue3DAxis*>
    SBK_QtGraphsWidgets_QList_QSurface3DSeriesPTR_IDX        = 4, // QList<QSurface3DSeries*>
    SBK_QtGraphsWidgets_QList_QScatter3DSeriesPTR_IDX        = 5, // QList<QScatter3DSeries*>
    SBK_QtGraphsWidgets_QList_QAbstract3DAxisPTR_IDX         = 6, // QList<QAbstract3DAxis*>
    SBK_QtGraphsWidgets_QList_QBar3DSeriesPTR_IDX            = 7, // QList<QBar3DSeries*>
    SBK_QtGraphsWidgets_QList_QVariant_IDX                   = 8, // QList<QVariant>
    SBK_QtGraphsWidgets_QList_QString_IDX                    = 9, // QList<QString>
    SBK_QtGraphsWidgets_QMap_QString_QVariant_IDX            = 10, // QMap<QString,QVariant>
    SBK_QtGraphsWidgets_CONVERTERS_IDX_COUNT                 = 11,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::Q3DBarsWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsWidgetsTypeStructs[SBK_Q3DBarsWidgetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::Q3DGraphsWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsWidgetsTypeStructs[SBK_Q3DGraphsWidgetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::Q3DScatterWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsWidgetsTypeStructs[SBK_Q3DScatterWidgetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::Q3DSurfaceWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtGraphsWidgetsTypeStructs[SBK_Q3DSurfaceWidgetItem_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTGRAPHSWIDGETS_PYTHON_H

