// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTPDF_PYTHON_H
#define SBK_QTPDF_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtgui_python.h>

// Bound library includes
#include <QtPdf/qpdfbookmarkmodel.h>
#include <QtPdf/qpdfdocument.h>
#include <QtPdf/qpdfdocumentrenderoptions.h>
#include <QtPdf/qpdflinkmodel.h>
#include <QtPdf/qpdfpagerenderer.h>
#include <QtPdf/qpdfsearchmodel.h>

QT_BEGIN_NAMESPACE
class QPdfLink;
class QPdfPageNavigator;
class QPdfSelection;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QPdfBookmarkModel_Role_IDX                           = 2,
    SBK_QPdfBookmarkModel_IDX                                = 1,
    SBK_QPdfDocument_Status_IDX                              = 7,
    SBK_QPdfDocument_Error_IDX                               = 4,
    SBK_QPdfDocument_MetaDataField_IDX                       = 5,
    SBK_QPdfDocument_PageModelRole_IDX                       = 6,
    SBK_QPdfDocument_IDX                                     = 3,
    SBK_QPdfDocumentRenderOptions_Rotation_IDX               = 10,
    SBK_QPdfDocumentRenderOptions_RenderFlag_IDX             = 9,
    SBK_QFlags_QPdfDocumentRenderOptions_RenderFlag_IDX      = 0,
    SBK_QPdfDocumentRenderOptions_IDX                        = 8,
    SBK_QPdfLink_IDX                                         = 11,
    SBK_QPdfLinkModel_Role_IDX                               = 13,
    SBK_QPdfLinkModel_IDX                                    = 12,
    SBK_QPdfPageNavigator_IDX                                = 14,
    SBK_QPdfPageRenderer_RenderMode_IDX                      = 16,
    SBK_QPdfPageRenderer_IDX                                 = 15,
    SBK_QPdfSearchModel_Role_IDX                             = 18,
    SBK_QPdfSearchModel_IDX                                  = 17,
    SBK_QPdfSelection_IDX                                    = 19,
    SBK_QtPdf_IDX_COUNT                                      = 20,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtPdfTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtPdfModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtPdfTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTPDF_QLIST_INT_IDX                                  = 0, // QList<int>
    SBK_QTPDF_QLIST_QPOLYGONF_IDX                            = 1, // QList<QPolygonF>
    SBK_QTPDF_QLIST_QRECTF_IDX                               = 2, // QList<QRectF>
    SBK_QTPDF_QMAP_INT_QVARIANT_IDX                          = 3, // QMap<int,QVariant>
    SBK_QTPDF_QLIST_QMODELINDEX_IDX                          = 4, // QList<QModelIndex>
    SBK_QTPDF_QHASH_INT_QBYTEARRAY_IDX                       = 5, // QHash<int,QByteArray>
    SBK_QTPDF_QLIST_QPDFLINK_IDX                             = 6, // QList<QPdfLink>
    SBK_QTPDF_QLIST_QVARIANT_IDX                             = 7, // QList<QVariant>
    SBK_QTPDF_QLIST_QSTRING_IDX                              = 8, // QList<QString>
    SBK_QTPDF_QMAP_QSTRING_QVARIANT_IDX                      = 9, // QMap<QString,QVariant>
    SBK_QTPDF_CONVERTERS_IDX_COUNT                           = 10,
};

// Converter indices
enum : int {
    SBK_QtPdf_QList_int_IDX                                  = 0, // QList<int>
    SBK_QtPdf_QList_QPolygonF_IDX                            = 1, // QList<QPolygonF>
    SBK_QtPdf_QList_QRectF_IDX                               = 2, // QList<QRectF>
    SBK_QtPdf_QMap_int_QVariant_IDX                          = 3, // QMap<int,QVariant>
    SBK_QtPdf_QList_QModelIndex_IDX                          = 4, // QList<QModelIndex>
    SBK_QtPdf_QHash_int_QByteArray_IDX                       = 5, // QHash<int,QByteArray>
    SBK_QtPdf_QList_QPdfLink_IDX                             = 6, // QList<QPdfLink>
    SBK_QtPdf_QList_QVariant_IDX                             = 7, // QList<QVariant>
    SBK_QtPdf_QList_QString_IDX                              = 8, // QList<QString>
    SBK_QtPdf_QMap_QString_QVariant_IDX                      = 9, // QMap<QString,QVariant>
    SBK_QtPdf_CONVERTERS_IDX_COUNT                           = 10,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QPdfBookmarkModel::Role >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfBookmarkModel_Role_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfBookmarkModel >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfBookmarkModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocument::Status >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocument_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocument::Error >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocument_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocument::MetaDataField >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocument_MetaDataField_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocument::PageModelRole >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocument_PageModelRole_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocument >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocument_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocumentRenderOptions::Rotation >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocumentRenderOptions_Rotation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocumentRenderOptions::RenderFlag >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocumentRenderOptions_RenderFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QPdfDocumentRenderOptions::RenderFlag> >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QFlags_QPdfDocumentRenderOptions_RenderFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfDocumentRenderOptions >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfDocumentRenderOptions_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfLink >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfLink_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfLinkModel::Role >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfLinkModel_Role_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfLinkModel >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfLinkModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfPageNavigator >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfPageNavigator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfPageRenderer::RenderMode >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfPageRenderer_RenderMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfPageRenderer >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfPageRenderer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfSearchModel::Role >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfSearchModel_Role_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfSearchModel >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfSearchModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPdfSelection >() { return Shiboken::Module::get(SbkPySide6_QtPdfTypeStructs[SBK_QPdfSelection_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTPDF_PYTHON_H

