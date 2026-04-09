// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTCANVASPAINTER_PYTHON_H
#define SBK_QTCANVASPAINTER_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtwidgets_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>
#include <pyside6_qtquick_python.h>
#include <pyside6_qtnetwork_python.h>
#include <pyside6_qtopengl_python.h>
#include <pyside6_qtqml_python.h>

// Bound library includes
#include <QtCanvasPainter/qcanvasbrush.h>
#include <QtCanvasPainter/qcanvasoffscreencanvas.h>
#include <QtCanvasPainter/qcanvaspainter.h>
#include <QtCanvasPainter/qcanvasrhipaintdriver.h>

QT_BEGIN_NAMESPACE
class QCanvasBoxGradient;
class QCanvasBoxShadow;
class QCanvasConicalGradient;
class QCanvasCustomBrush;
class QCanvasGradient;
class QCanvasGridPattern;
class QCanvasImage;
class QCanvasImagePattern;
class QCanvasLinearGradient;
class QCanvasPainterFactory;
class QCanvasPainterItem;
class QCanvasPainterItemRenderer;
class QCanvasPainterWidget;
class QCanvasPath;
class QCanvasRadialGradient;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QCanvasBoxGradient_IDX                               = 0,
    SBK_QCanvasBoxShadow_IDX                                 = 1,
    SBK_QCanvasBrush_BrushType_IDX                           = 3,
    SBK_QCanvasBrush_IDX                                     = 2,
    SBK_QCanvasConicalGradient_IDX                           = 4,
    SBK_QCanvasCustomBrush_IDX                               = 5,
    SBK_QCanvasGradient_IDX                                  = 6,
    SBK_QCanvasGridPattern_IDX                               = 7,
    SBK_QCanvasImage_IDX                                     = 8,
    SBK_QCanvasImagePattern_IDX                              = 9,
    SBK_QCanvasLinearGradient_IDX                            = 10,
    SBK_QCanvasOffscreenCanvas_Flag_IDX                      = 12,
    SBK_QFlags_QCanvasOffscreenCanvas_Flag_IDX               = 34,
    SBK_QCanvasOffscreenCanvas_IDX                           = 11,
    SBK_QCanvasPainter_PathWinding_IDX                       = 19,
    SBK_QCanvasPainter_PathConnection_IDX                    = 18,
    SBK_QCanvasPainter_LineCap_IDX                           = 16,
    SBK_QCanvasPainter_LineJoin_IDX                          = 17,
    SBK_QCanvasPainter_TextAlign_IDX                         = 21,
    SBK_QCanvasPainter_TextBaseline_IDX                      = 22,
    SBK_QCanvasPainter_TextDirection_IDX                     = 23,
    SBK_QCanvasPainter_CompositeOperation_IDX                = 14,
    SBK_QCanvasPainter_WrapMode_IDX                          = 24,
    SBK_QCanvasPainter_ImageFlag_IDX                         = 15,
    SBK_QFlags_QCanvasPainter_ImageFlag_IDX                  = 35,
    SBK_QCanvasPainter_RenderHint_IDX                        = 20,
    SBK_QFlags_QCanvasPainter_RenderHint_IDX                 = 36,
    SBK_QCanvasPainter_IDX                                   = 13,
    SBK_QCanvasPainterFactory_IDX                            = 25,
    SBK_QCanvasPainterItem_IDX                               = 26,
    SBK_QCanvasPainterItemRenderer_IDX                       = 27,
    SBK_QCanvasPainterWidget_IDX                             = 28,
    SBK_QCanvasPath_IDX                                      = 29,
    SBK_QCanvasRadialGradient_IDX                            = 30,
    SBK_QCanvasRhiPaintDriver_BeginPaintFlag_IDX             = 32,
    SBK_QFlags_QCanvasRhiPaintDriver_BeginPaintFlag_IDX      = 37,
    SBK_QCanvasRhiPaintDriver_EndPaintFlag_IDX               = 33,
    SBK_QFlags_QCanvasRhiPaintDriver_EndPaintFlag_IDX        = 38,
    SBK_QCanvasRhiPaintDriver_IDX                            = 31,
    SBK_QtCanvasPainter_IDX_COUNT                            = 39,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtCanvasPainterTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtCanvasPainterModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtCanvasPainterTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTCANVASPAINTER_QLIST_INT_IDX                        = 0, // QList<int>
    SBK_QTCANVASPAINTER_QMAP_QSTRING_QVARIANT_IDX            = 1, // QMap<QString,QVariant>
    SBK_QTCANVASPAINTER_QLIST_QVARIANT_IDX                   = 2, // QList<QVariant>
    SBK_QTCANVASPAINTER_QLIST_QSTRING_IDX                    = 3, // QList<QString>
    SBK_QTCANVASPAINTER_CONVERTERS_IDX_COUNT                 = 4,
};

// Converter indices
enum : int {
    SBK_QtCanvasPainter_QList_int_IDX                        = 0, // QList<int>
    SBK_QtCanvasPainter_QMap_QString_QVariant_IDX            = 1, // QMap<QString,QVariant>
    SBK_QtCanvasPainter_QList_QVariant_IDX                   = 2, // QList<QVariant>
    SBK_QtCanvasPainter_QList_QString_IDX                    = 3, // QList<QString>
    SBK_QtCanvasPainter_CONVERTERS_IDX_COUNT                 = 4,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QCanvasBoxGradient >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasBoxGradient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasBoxShadow >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasBoxShadow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasBrush::BrushType >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasBrush_BrushType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasBrush >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasBrush_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasConicalGradient >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasConicalGradient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasCustomBrush >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasCustomBrush_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasGradient >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasGradient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasGridPattern >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasGridPattern_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasImage >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasImage_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasImagePattern >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasImagePattern_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasLinearGradient >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasLinearGradient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasOffscreenCanvas::Flag >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasOffscreenCanvas_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanvasOffscreenCanvas::Flag> >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QFlags_QCanvasOffscreenCanvas_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasOffscreenCanvas >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasOffscreenCanvas_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::PathWinding >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_PathWinding_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::PathConnection >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_PathConnection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::LineCap >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_LineCap_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::LineJoin >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_LineJoin_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::TextAlign >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_TextAlign_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::TextBaseline >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_TextBaseline_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::TextDirection >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_TextDirection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::CompositeOperation >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_CompositeOperation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::WrapMode >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_WrapMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::ImageFlag >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_ImageFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanvasPainter::ImageFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QFlags_QCanvasPainter_ImageFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter::RenderHint >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_RenderHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanvasPainter::RenderHint> >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QFlags_QCanvasPainter_RenderHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainter >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainterFactory >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainterFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainterItem >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainterItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainterItemRenderer >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainterItemRenderer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPainterWidget >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPainterWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasPath >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasPath_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasRadialGradient >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasRadialGradient_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasRhiPaintDriver::BeginPaintFlag >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasRhiPaintDriver_BeginPaintFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanvasRhiPaintDriver::BeginPaintFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QFlags_QCanvasRhiPaintDriver_BeginPaintFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasRhiPaintDriver::EndPaintFlag >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasRhiPaintDriver_EndPaintFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCanvasRhiPaintDriver::EndPaintFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QFlags_QCanvasRhiPaintDriver_EndPaintFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCanvasRhiPaintDriver >() { return Shiboken::Module::get(SbkPySide6_QtCanvasPainterTypeStructs[SBK_QCanvasRhiPaintDriver_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTCANVASPAINTER_PYTHON_H

