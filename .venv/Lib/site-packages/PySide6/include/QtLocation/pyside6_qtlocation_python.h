// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTLOCATION_PYTHON_H
#define SBK_QTLOCATION_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtcore_python.h>
#include <pyside6_qtpositioning_python.h>

// Bound library includes
#include <QtLocation/qgeocodereply.h>
#include <QtLocation/qgeomaneuver.h>
#include <QtLocation/qgeoroutereply.h>
#include <QtLocation/qgeorouterequest.h>
#include <QtLocation/qgeoserviceprovider.h>
#include <QtLocation/qlocation.h>
#include <QtLocation/qplacecontent.h>
#include <QtLocation/qplaceidreply.h>
#include <QtLocation/qplacereply.h>
#include <QtLocation/qplacesearchrequest.h>
#include <QtLocation/qplacesearchresult.h>

QT_BEGIN_NAMESPACE
class QGeoCodingManager;
class QGeoCodingManagerEngine;
class QGeoRoute;
class QGeoRouteSegment;
class QGeoRoutingManager;
class QGeoRoutingManagerEngine;
class QGeoServiceProviderFactory;
class QPlace;
class QPlaceAttribute;
class QPlaceCategory;
class QPlaceContactDetail;
class QPlaceContentReply;
class QPlaceContentRequest;
class QPlaceDetailsReply;
class QPlaceIcon;
class QPlaceManager;
class QPlaceManagerEngine;
class QPlaceMatchReply;
class QPlaceMatchRequest;
class QPlaceProposedSearchResult;
class QPlaceRatings;
class QPlaceResult;
class QPlaceSearchReply;
class QPlaceSearchSuggestionReply;
class QPlaceSupplier;
class QPlaceUser;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QGeoCodeReply_Error_IDX                              = 13,
    SBK_QGeoCodeReply_IDX                                    = 12,
    SBK_QGeoCodingManager_IDX                                = 14,
    SBK_QGeoCodingManagerEngine_IDX                          = 15,
    SBK_QGeoManeuver_InstructionDirection_IDX                = 17,
    SBK_QGeoManeuver_IDX                                     = 16,
    SBK_QGeoRoute_IDX                                        = 18,
    SBK_QGeoRouteReply_Error_IDX                             = 20,
    SBK_QGeoRouteReply_IDX                                   = 19,
    SBK_QGeoRouteRequest_TravelMode_IDX                      = 27,
    SBK_QFlags_QGeoRouteRequest_TravelMode_IDX               = 5,
    SBK_QGeoRouteRequest_FeatureType_IDX                     = 22,
    SBK_QFlags_QGeoRouteRequest_FeatureType_IDX              = 0,
    SBK_QGeoRouteRequest_FeatureWeight_IDX                   = 23,
    SBK_QFlags_QGeoRouteRequest_FeatureWeight_IDX            = 1,
    SBK_QGeoRouteRequest_RouteOptimization_IDX               = 25,
    SBK_QFlags_QGeoRouteRequest_RouteOptimization_IDX        = 3,
    SBK_QGeoRouteRequest_SegmentDetail_IDX                   = 26,
    SBK_QFlags_QGeoRouteRequest_SegmentDetail_IDX            = 4,
    SBK_QGeoRouteRequest_ManeuverDetail_IDX                  = 24,
    SBK_QFlags_QGeoRouteRequest_ManeuverDetail_IDX           = 2,
    SBK_QGeoRouteRequest_IDX                                 = 21,
    SBK_QGeoRouteSegment_IDX                                 = 28,
    SBK_QGeoRoutingManager_IDX                               = 29,
    SBK_QGeoRoutingManagerEngine_IDX                         = 30,
    SBK_QGeoServiceProvider_Error_IDX                        = 32,
    SBK_QGeoServiceProvider_RoutingFeature_IDX               = 37,
    SBK_QFlags_QGeoServiceProvider_RoutingFeature_IDX        = 10,
    SBK_QGeoServiceProvider_GeocodingFeature_IDX             = 33,
    SBK_QFlags_QGeoServiceProvider_GeocodingFeature_IDX      = 6,
    SBK_QGeoServiceProvider_MappingFeature_IDX               = 34,
    SBK_QFlags_QGeoServiceProvider_MappingFeature_IDX        = 7,
    SBK_QGeoServiceProvider_PlacesFeature_IDX                = 36,
    SBK_QFlags_QGeoServiceProvider_PlacesFeature_IDX         = 9,
    SBK_QGeoServiceProvider_NavigationFeature_IDX            = 35,
    SBK_QFlags_QGeoServiceProvider_NavigationFeature_IDX     = 8,
    SBK_QGeoServiceProvider_IDX                              = 31,
    SBK_QGeoServiceProviderFactory_IDX                       = 38,
    SBK_QLocation_Visibility_IDX                             = 40,
    SBK_QFlags_QLocation_Visibility_IDX                      = 11,
    SBK_QtLocationQLocation_IDX                              = 39,
    SBK_QPlace_IDX                                           = 41,
    SBK_QPlaceAttribute_IDX                                  = 42,
    SBK_QPlaceCategory_IDX                                   = 43,
    SBK_QPlaceContactDetail_IDX                              = 44,
    SBK_QPlaceContent_Type_IDX                               = 47,
    SBK_QPlaceContent_DataTag_IDX                            = 46,
    SBK_QPlaceContent_IDX                                    = 45,
    SBK_QPlaceContentReply_IDX                               = 48,
    SBK_QPlaceContentRequest_IDX                             = 49,
    SBK_QPlaceDetailsReply_IDX                               = 50,
    SBK_QPlaceIcon_IDX                                       = 51,
    SBK_QPlaceIdReply_OperationType_IDX                      = 53,
    SBK_QPlaceIdReply_IDX                                    = 52,
    SBK_QPlaceManager_IDX                                    = 54,
    SBK_QPlaceManagerEngine_IDX                              = 55,
    SBK_QPlaceMatchReply_IDX                                 = 56,
    SBK_QPlaceMatchRequest_IDX                               = 57,
    SBK_QPlaceProposedSearchResult_IDX                       = 58,
    SBK_QPlaceRatings_IDX                                    = 59,
    SBK_QPlaceReply_Error_IDX                                = 61,
    SBK_QPlaceReply_Type_IDX                                 = 62,
    SBK_QPlaceReply_IDX                                      = 60,
    SBK_QPlaceResult_IDX                                     = 63,
    SBK_QPlaceSearchReply_IDX                                = 64,
    SBK_QPlaceSearchRequest_RelevanceHint_IDX                = 66,
    SBK_QPlaceSearchRequest_IDX                              = 65,
    SBK_QPlaceSearchResult_SearchResultType_IDX              = 68,
    SBK_QPlaceSearchResult_IDX                               = 67,
    SBK_QPlaceSearchSuggestionReply_IDX                      = 69,
    SBK_QPlaceSupplier_IDX                                   = 70,
    SBK_QPlaceUser_IDX                                       = 71,
    SBK_QtLocation_IDX_COUNT                                 = 72,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtLocationTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtLocationModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtLocationTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTLOCATION_QLIST_INT_IDX                             = 0, // QList<int>
    SBK_QTLOCATION_QLIST_QPLACECATEGORY_IDX                  = 1, // QList<QPlaceCategory>
    SBK_QTLOCATION_QMAP_QSTRING_QVARIANT_IDX                 = 2, // QMap<QString,QVariant>
    SBK_QTLOCATION_QLIST_QPLACE_IDX                          = 3, // QList<QPlace>
    SBK_QTLOCATION_QLIST_QPLACESEARCHRESULT_IDX              = 4, // QList<QPlaceSearchResult>
    SBK_QTLOCATION_QLIST_QPLACECONTENT_DATATAG_IDX           = 5, // QList<QPlaceContent::DataTag>
    SBK_QTLOCATION_QLIST_QPLACECONTACTDETAIL_IDX             = 6, // QList<QPlaceContactDetail>
    SBK_QTLOCATION_QMAP_INT_QPLACECONTENT_IDX                = 7, // QMap<int,QPlaceContent>
    SBK_QTLOCATION_QLIST_QGEOCOORDINATE_IDX                  = 8, // QList<QGeoCoordinate>
    SBK_QTLOCATION_QLIST_QGEORECTANGLE_IDX                   = 9, // QList<QGeoRectangle>
    SBK_QTLOCATION_QLIST_QGEOROUTEREQUEST_FEATURETYPE_IDX    = 10, // QList<QGeoRouteRequest::FeatureType>
    SBK_QTLOCATION_QLIST_QGEOROUTE_IDX                       = 11, // QList<QGeoRoute>
    SBK_QTLOCATION_QLIST_QGEOROUTESEGMENT_IDX                = 12, // QList<QGeoRouteSegment>
    SBK_QTLOCATION_QLIST_QLOCALE_IDX                         = 13, // QList<QLocale>
    SBK_QTLOCATION_QLIST_QGEOLOCATION_IDX                    = 14, // QList<QGeoLocation>
    SBK_QTLOCATION_QLIST_QVARIANT_IDX                        = 15, // QList<QVariant>
    SBK_QTLOCATION_QLIST_QSTRING_IDX                         = 16, // QList<QString>
    SBK_QTLOCATION_CONVERTERS_IDX_COUNT                      = 17,
};

// Converter indices
enum : int {
    SBK_QtLocation_QList_int_IDX                             = 0, // QList<int>
    SBK_QtLocation_QList_QPlaceCategory_IDX                  = 1, // QList<QPlaceCategory>
    SBK_QtLocation_QMap_QString_QVariant_IDX                 = 2, // QMap<QString,QVariant>
    SBK_QtLocation_QList_QPlace_IDX                          = 3, // QList<QPlace>
    SBK_QtLocation_QList_QPlaceSearchResult_IDX              = 4, // QList<QPlaceSearchResult>
    SBK_QtLocation_QList_QPlaceContent_DataTag_IDX           = 5, // QList<QPlaceContent::DataTag>
    SBK_QtLocation_QList_QPlaceContactDetail_IDX             = 6, // QList<QPlaceContactDetail>
    SBK_QtLocation_QMap_int_QPlaceContent_IDX                = 7, // QMap<int,QPlaceContent>
    SBK_QtLocation_QList_QGeoCoordinate_IDX                  = 8, // QList<QGeoCoordinate>
    SBK_QtLocation_QList_QGeoRectangle_IDX                   = 9, // QList<QGeoRectangle>
    SBK_QtLocation_QList_QGeoRouteRequest_FeatureType_IDX    = 10, // QList<QGeoRouteRequest::FeatureType>
    SBK_QtLocation_QList_QGeoRoute_IDX                       = 11, // QList<QGeoRoute>
    SBK_QtLocation_QList_QGeoRouteSegment_IDX                = 12, // QList<QGeoRouteSegment>
    SBK_QtLocation_QList_QLocale_IDX                         = 13, // QList<QLocale>
    SBK_QtLocation_QList_QGeoLocation_IDX                    = 14, // QList<QGeoLocation>
    SBK_QtLocation_QList_QVariant_IDX                        = 15, // QList<QVariant>
    SBK_QtLocation_QList_QString_IDX                         = 16, // QList<QString>
    SBK_QtLocation_CONVERTERS_IDX_COUNT                      = 17,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QGeoCodeReply::Error >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoCodeReply_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoCodeReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoCodeReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoCodingManager >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoCodingManager_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoCodingManagerEngine >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoCodingManagerEngine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoManeuver::InstructionDirection >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoManeuver_InstructionDirection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoManeuver >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoManeuver_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRoute >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRoute_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteReply::Error >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteReply_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteRequest::TravelMode >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteRequest_TravelMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoRouteRequest::TravelMode> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoRouteRequest_TravelMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteRequest::FeatureType >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteRequest_FeatureType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoRouteRequest::FeatureType> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoRouteRequest_FeatureType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteRequest::FeatureWeight >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteRequest_FeatureWeight_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoRouteRequest::FeatureWeight> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoRouteRequest_FeatureWeight_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteRequest::RouteOptimization >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteRequest_RouteOptimization_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoRouteRequest::RouteOptimization> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoRouteRequest_RouteOptimization_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteRequest::SegmentDetail >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteRequest_SegmentDetail_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoRouteRequest::SegmentDetail> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoRouteRequest_SegmentDetail_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteRequest::ManeuverDetail >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteRequest_ManeuverDetail_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoRouteRequest::ManeuverDetail> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoRouteRequest_ManeuverDetail_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteRequest >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteRequest_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRouteSegment >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRouteSegment_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRoutingManager >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRoutingManager_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoRoutingManagerEngine >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoRoutingManagerEngine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProvider::Error >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProvider_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProvider::RoutingFeature >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProvider_RoutingFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoServiceProvider::RoutingFeature> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoServiceProvider_RoutingFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProvider::GeocodingFeature >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProvider_GeocodingFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoServiceProvider::GeocodingFeature> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoServiceProvider_GeocodingFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProvider::MappingFeature >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProvider_MappingFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoServiceProvider::MappingFeature> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoServiceProvider_MappingFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProvider::PlacesFeature >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProvider_PlacesFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoServiceProvider::PlacesFeature> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoServiceProvider_PlacesFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProvider::NavigationFeature >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProvider_NavigationFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGeoServiceProvider::NavigationFeature> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QGeoServiceProvider_NavigationFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProvider >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProvider_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGeoServiceProviderFactory >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QGeoServiceProviderFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocation::Visibility >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QLocation_Visibility_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QLocation::Visibility> >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QFlags_QLocation_Visibility_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlace >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlace_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceAttribute >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceAttribute_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceCategory >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceCategory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceContactDetail >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceContactDetail_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceContent::Type >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceContent_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceContent::DataTag >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceContent_DataTag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceContent >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceContent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceContentReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceContentReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceContentRequest >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceContentRequest_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceDetailsReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceDetailsReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceIcon >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceIcon_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceIdReply::OperationType >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceIdReply_OperationType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceIdReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceIdReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceManager >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceManager_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceManagerEngine >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceManagerEngine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceMatchReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceMatchReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceMatchRequest >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceMatchRequest_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceProposedSearchResult >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceProposedSearchResult_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceRatings >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceRatings_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceReply::Error >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceReply_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceReply::Type >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceReply_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceResult >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceResult_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceSearchReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceSearchReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceSearchRequest::RelevanceHint >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceSearchRequest_RelevanceHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceSearchRequest >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceSearchRequest_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceSearchResult::SearchResultType >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceSearchResult_SearchResultType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceSearchResult >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceSearchResult_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceSearchSuggestionReply >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceSearchSuggestionReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceSupplier >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceSupplier_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlaceUser >() { return Shiboken::Module::get(SbkPySide6_QtLocationTypeStructs[SBK_QPlaceUser_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTLOCATION_PYTHON_H

