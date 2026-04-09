// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTCORE_PYTHON_H
#define SBK_QTCORE_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Bound library includes
#include <qabstractanimation.h>
#include <qabstracteventdispatcher.h>
#include <qabstractitemmodel.h>
#include <qbytearray.h>
#include <qcalendar.h>
#include <qcborcommon.h>
#include <qcborstream.h>
#include <qcborstreamreader.h>
#include <qcborvalue.h>
#include <qcommandlineoption.h>
#include <qcommandlineparser.h>
#include <qcompare.h>
#include <qcoreapplication.h>
#include <qcoreevent.h>
#include <qcryptographichash.h>
#include <qdatastream.h>
#include <qdatetime.h>
#include <qdeadlinetimer.h>
#include <qdir.h>
#include <qdiriterator.h>
#include <qdirlisting.h>
#include <qeasingcurve.h>
#include <qelapsedtimer.h>
#include <qeventloop.h>
#include <qfiledevice.h>
#include <qiodevicebase.h>
#include <qitemselectionmodel.h>
#include <qjsondocument.h>
#include <qjsonparseerror.h>
#include <qjsonvalue.h>
#include <qlibrary.h>
#include <qlibraryinfo.h>
#include <qline.h>
#include <qlocale.h>
#include <qlockfile.h>
#include <qlogging.h>
#include <qmetaobject.h>
#include <qmetatype.h>
#include <qmimedatabase.h>
#include <qnamespace.h>
#include <qobjectdefs.h>
#include <qoperatingsystemversion.h>
#include <qrangemodel.h>
#include <qreadwritelock.h>
#include <qregularexpression.h>
#include <qresource.h>
#include <qsettings.h>
#include <qsocketnotifier.h>
#include <qsortfilterproxymodel.h>
#include <qstandardpaths.h>
#include <qstringconverter_base.h>
#include <qsysinfo.h>
#include <qtextboundaryfinder.h>
#include <qtextstream.h>
#include <qtimeline.h>
#include <qtipccommon.h>
#include <qurl.h>
#include <quuid.h>
#include <qversionnumber.h>
#include <qxmlstream.h>
#if QT_CONFIG(future)
#include <qfutureinterface.h>
#endif
#if QT_CONFIG(permissions)
#include <qpermissions.h>
#endif
#if QT_CONFIG(process)
#include <qprocess.h>
#endif
#if QT_CONFIG(processenvironment)
#include <qprocess.h>
#endif
#if QT_CONFIG(sharedmemory)
#include <qsharedmemory.h>
#endif
#if QT_CONFIG(systemsemaphore)
#include <qsystemsemaphore.h>
#endif
#if QT_CONFIG(thread)
#include <qthread.h>
#endif
#if QT_CONFIG(timezone)
#include <qtimezone.h>
#endif

QT_BEGIN_NAMESPACE
class QAbstractListModel;
class QAbstractNativeEventFilter;
class QAbstractProxyModel;
class QAbstractTableModel;
class QAnimationGroup;
class QBasicMutex;
class QBasicReadWriteLock;
class QBasicTimer;
class QBitArray;
class QBuffer;
class QByteArrayMatcher;
class QCameraPermission;
class QCborArray;
class QCborMap;
struct QCborParserError;
class QCborStreamWriter;
class QChildEvent;
class QCollator;
class QCollatorSortKey;
class QConcatenateTablesProxyModel;
class QDate;
class QDynamicPropertyChangeEvent;
struct QFactoryInterface;
class QFile;
class QFileInfo;
class QFileSelector;
class QFileSystemWatcher;
class QGenericArgument;
class QGenericReturnArgument;
struct QHashSeed;
class QIODevice;
class QIdentityProxyModel;
class QItemSelection;
class QItemSelectionRange;
class QJsonArray;
class QKeyCombination;
class QLine;
class QLoggingCategory;
class QMargins;
class QMarginsF;
class QMessageAuthenticationCode;
class QMessageLogContext;
class QMessageLogger;
class QMetaClassInfo;
class QMetaEnum;
class QMetaProperty;
class QMicrophonePermission;
class QMimeData;
class QMimeType;
class QModelIndex;
class QModelRoleData;
class QModelRoleDataSpan;
class QMutex;
class QObject;
class QOperatingSystemVersionBase;
class QParallelAnimationGroup;
class QPauseAnimation;
class QPermission;
class QPersistentModelIndex;
class QPluginLoader;
class QPoint;
class QPointF;
class QPropertyAnimation;
class QRandomGenerator;
class QRandomGenerator64;
class QReadLocker;
class QRect;
class QRectF;
class QRecursiveMutex;
class QRegularExpressionMatch;
class QRegularExpressionMatchIterator;
class QRunnable;
class QSaveFile;
class QSemaphore;
class QSemaphoreReleaser;
class QSequentialAnimationGroup;
class QSignalBlocker;
class QSignalMapper;
class QSize;
class QSizeF;
class QSocketDescriptor;
class QStorageInfo;
class QStringDecoder;
class QStringEncoder;
class QStringListModel;
class QTemporaryDir;
class QTemporaryFile;
class QTextStreamManipulator;
class QThreadPool;
class QTimer;
class QTimerEvent;
class QTranslator;
class QTransposeProxyModel;
class QUrlQuery;
class QVariantAnimation;
class QWaitCondition;
class QWinEventNotifier;
class QWriteLocker;
class QXmlStreamAttribute;
class QXmlStreamAttributes;
class QXmlStreamEntityDeclaration;
class QXmlStreamEntityResolver;
class QXmlStreamNamespaceDeclaration;
class QXmlStreamNotationDeclaration;

namespace QtCoreHelper {
    class QDirListingIterator;
    class QGenericArgumentHolder;
    class QGenericReturnArgumentHolder;
    class QIOPipe;
    class QMutexLocker;
}
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractAnimation_Direction_IDX                     = 2,
    SBK_QAbstractAnimation_State_IDX                         = 3,
    SBK_QAbstractAnimation_DeletionPolicy_IDX                = 1,
    SBK_QAbstractAnimation_IDX                               = 0,
    SBK_QAbstractEventDispatcher_IDX                         = 4,
    SBK_QAbstractEventDispatcher_TimerInfo_IDX               = 5,
    SBK_QAbstractItemModel_LayoutChangeHint_IDX              = 8,
    SBK_QAbstractItemModel_CheckIndexOption_IDX              = 7,
    SBK_QFlags_QAbstractItemModel_CheckIndexOption_IDX       = 106,
    SBK_QAbstractItemModel_IDX                               = 6,
    SBK_QAbstractListModel_IDX                               = 9,
    SBK_QAbstractNativeEventFilter_IDX                       = 10,
    SBK_QAbstractProxyModel_IDX                              = 11,
    SBK_QAbstractTableModel_IDX                              = 12,
    SBK_QAnimationGroup_IDX                                  = 13,
    SBK_QBasicMutex_IDX                                      = 14,
    SBK_QBasicReadWriteLock_IDX                              = 15,
    SBK_QBasicTimer_IDX                                      = 16,
    SBK_QBitArray_IDX                                        = 17,
    SBK_QBluetoothPermission_CommunicationMode_IDX           = 19,
    SBK_QFlags_QBluetoothPermission_CommunicationMode_IDX    = 107,
    SBK_QBluetoothPermission_IDX                             = 18,
    SBK_QBuffer_IDX                                          = 20,
    SBK_QByteArray_Base64Option_IDX                          = 23,
    SBK_QFlags_QByteArray_Base64Option_IDX                   = 108,
    SBK_QByteArray_Base64DecodingStatus_IDX                  = 22,
    SBK_QByteArray_IDX                                       = 21,
    SBK_QByteArray_FromBase64Result_IDX                      = 24,
    SBK_QByteArrayMatcher_IDX                                = 25,
    SBK_QCalendar_Unspecified_IDX                            = 29,
    SBK_QCalendar_System_IDX                                 = 27,
    SBK_QCalendar_IDX                                        = 26,
    SBK_QCalendar_SystemId_IDX                               = 28,
    SBK_QCalendar_YearMonthDay_IDX                           = 30,
    SBK_QCalendarPermission_AccessMode_IDX                   = 32,
    SBK_QCalendarPermission_IDX                              = 31,
    SBK_QCameraPermission_IDX                                = 33,
    SBK_QCborArray_IDX                                       = 34,
    SBK_QCborError_Code_IDX                                  = 36,
    SBK_QCborError_IDX                                       = 35,
    SBK_QCborMap_IDX                                         = 38,
    SBK_QCborParserError_IDX                                 = 39,
    SBK_QCborStreamReader_Type_IDX                           = 43,
    SBK_QCborStreamReader_StringResultCode_IDX               = 42,
    SBK_QCborStreamReader_IDX                                = 41,
    SBK_QCborStreamWriter_IDX                                = 44,
    SBK_QCborStringResultByteArray_IDX                       = 45,
    SBK_QCborStreamReader_StringResult_QByteArray_IDX        = 45,
    SBK_QCborStringResultString_IDX                          = 46,
    SBK_QCborStreamReader_StringResult_QString_IDX           = 46,
    SBK_QCborValue_EncodingOption_IDX                        = 50,
    SBK_QFlags_QCborValue_EncodingOption_IDX                 = 110,
    SBK_QCborValue_DiagnosticNotationOption_IDX              = 49,
    SBK_QFlags_QCborValue_DiagnosticNotationOption_IDX       = 109,
    SBK_QCborValue_Type_IDX                                  = 51,
    SBK_QCborValue_IDX                                       = 48,
    SBK_QChildEvent_IDX                                      = 52,
    SBK_QCollator_IDX                                        = 53,
    SBK_QCollatorSortKey_IDX                                 = 54,
    SBK_QCommandLineOption_Flag_IDX                          = 56,
    SBK_QFlags_QCommandLineOption_Flag_IDX                   = 111,
    SBK_QCommandLineOption_IDX                               = 55,
    SBK_QCommandLineParser_SingleDashWordOptionMode_IDX      = 60,
    SBK_QCommandLineParser_OptionsAfterPositionalArgumentsMode_IDX = 59,
    SBK_QCommandLineParser_MessageType_IDX                   = 58,
    SBK_QCommandLineParser_IDX                               = 57,
    SBK_QConcatenateTablesProxyModel_IDX                     = 61,
    SBK_QContactsPermission_AccessMode_IDX                   = 63,
    SBK_QContactsPermission_IDX                              = 62,
    SBK_QCoreApplication_ApplicationFlags_IDX                = 472,
    SBK_QCoreApplication_IDX                                 = 64,
    SBK_QCryptographicHash_Algorithm_IDX                     = 66,
    SBK_QCryptographicHash_IDX                               = 65,
    SBK_QDataStream_Version_IDX                              = 71,
    SBK_QDataStream_ByteOrder_IDX                            = 68,
    SBK_QDataStream_Status_IDX                               = 70,
    SBK_QDataStream_FloatingPointPrecision_IDX               = 69,
    SBK_QDataStream_IDX                                      = 67,
    SBK_QDate_IDX                                            = 72,
    SBK_QDateTime_TransitionResolution_IDX                   = 74,
    SBK_QDateTime_YearRange_IDX                              = 75,
    SBK_QDateTime_IDX                                        = 73,
    SBK_QDeadlineTimer_ForeverConstant_IDX                   = 77,
    SBK_QDeadlineTimer_IDX                                   = 76,
    SBK_QDir_Filter_IDX                                      = 79,
    SBK_QFlags_QDir_Filter_IDX                               = 112,
    SBK_QDir_SortFlag_IDX                                    = 80,
    SBK_QFlags_QDir_SortFlag_IDX                             = 113,
    SBK_QDir_IDX                                             = 78,
    SBK_QDirIterator_IteratorFlag_IDX                        = 82,
    SBK_QFlags_QDirIterator_IteratorFlag_IDX                 = 114,
    SBK_QDirIterator_IDX                                     = 81,
    SBK_QDirListing_IteratorFlag_IDX                         = 85,
    SBK_QFlags_QDirListing_IteratorFlag_IDX                  = 115,
    SBK_QDirListing_IDX                                      = 83,
    SBK_QDirListing_DirEntry_IDX                             = 84,
    SBK_QDynamicPropertyChangeEvent_IDX                      = 86,
    SBK_QEasingCurve_Type_IDX                                = 88,
    SBK_QEasingCurve_IDX                                     = 87,
    SBK_QElapsedTimer_ClockType_IDX                          = 90,
    SBK_QElapsedTimer_IDX                                    = 89,
    SBK_QEvent_Type_IDX                                      = 92,
    SBK_QEvent_IDX                                           = 91,
    SBK_QEventLoop_ProcessEventsFlag_IDX                     = 94,
    SBK_QFlags_QEventLoop_ProcessEventsFlag_IDX              = 116,
    SBK_QEventLoop_IDX                                       = 93,
    SBK_QFactoryInterface_IDX                                = 95,
    SBK_QFile_IDX                                            = 96,
    SBK_QFileDevice_FileError_IDX                            = 98,
    SBK_QFileDevice_FileTime_IDX                             = 100,
    SBK_QFileDevice_Permission_IDX                           = 102,
    SBK_QFlags_QFileDevice_Permission_IDX                    = 119,
    SBK_QFileDevice_FileHandleFlag_IDX                       = 99,
    SBK_QFlags_QFileDevice_FileHandleFlag_IDX                = 117,
    SBK_QFileDevice_MemoryMapFlag_IDX                        = 101,
    SBK_QFlags_QFileDevice_MemoryMapFlag_IDX                 = 118,
    SBK_QFileDevice_IDX                                      = 97,
    SBK_QFileInfo_IDX                                        = 103,
    SBK_QFileSelector_IDX                                    = 104,
    SBK_QFileSystemWatcher_IDX                               = 105,
    SBK_QFutureInterfaceBase_State_IDX                       = 165,
    SBK_QFutureInterfaceBase_ContinuationType_IDX            = 164,
    SBK_QFutureInterfaceBase_CancelMode_IDX                  = 163,
    SBK_QFutureInterfaceBase_IDX                             = 162,
    SBK_QGenericArgument_IDX                                 = 166,
    SBK_QGenericReturnArgument_IDX                           = 167,
    SBK_QHashSeed_IDX                                        = 168,
    SBK_QIODevice_IDX                                        = 169,
    SBK_QIODeviceBase_OpenModeFlag_IDX                       = 171,
    SBK_QFlags_QIODeviceBase_OpenModeFlag_IDX                = 120,
    SBK_QIODeviceBase_IDX                                    = 170,
    SBK_QIdentityProxyModel_IDX                              = 172,
    SBK_QItemSelection_IDX                                   = 173,
    SBK_QItemSelectionModel_SelectionFlag_IDX                = 175,
    SBK_QFlags_QItemSelectionModel_SelectionFlag_IDX         = 121,
    SBK_QItemSelectionModel_IDX                              = 174,
    SBK_QItemSelectionRange_IDX                              = 176,
    SBK_QJsonArray_IDX                                       = 177,
    SBK_QJsonDocument_JsonFormat_IDX                         = 179,
    SBK_QJsonDocument_IDX                                    = 178,
    SBK_QJsonParseError_ParseError_IDX                       = 181,
    SBK_QJsonParseError_IDX                                  = 180,
    SBK_QJsonValue_Type_IDX                                  = 183,
    SBK_QJsonValue_IDX                                       = 182,
    SBK_QKeyCombination_IDX                                  = 184,
    SBK_QLibrary_LoadHint_IDX                                = 186,
    SBK_QFlags_QLibrary_LoadHint_IDX                         = 122,
    SBK_QLibrary_IDX                                         = 185,
    SBK_QLibraryInfo_LibraryPath_IDX                         = 188,
    SBK_QLibraryInfo_IDX                                     = 187,
    SBK_QLine_IDX                                            = 189,
    SBK_QLineF_IntersectionType_IDX                          = 191,
    SBK_QLineF_IDX                                           = 190,
    SBK_QLocale_Language_IDX                                 = 197,
    SBK_QLocale_Script_IDX                                   = 475,
    SBK_QLocale_Country_IDX                                  = 193,
    SBK_QLocale_MeasurementSystem_IDX                        = 199,
    SBK_QLocale_FormatType_IDX                               = 196,
    SBK_QLocale_NumberOption_IDX                             = 200,
    SBK_QFlags_QLocale_NumberOption_IDX                      = 125,
    SBK_QLocale_FloatingPointPrecisionOption_IDX             = 195,
    SBK_QLocale_TagSeparator_IDX                             = 201,
    SBK_QLocale_CurrencySymbolFormat_IDX                     = 473,
    SBK_QLocale_DataSizeFormat_IDX                           = 194,
    SBK_QFlags_QLocale_DataSizeFormat_IDX                    = 123,
    SBK_QLocale_LanguageCodeType_IDX                         = 198,
    SBK_QFlags_QLocale_LanguageCodeType_IDX                  = 124,
    SBK_QLocale_QuotationStyle_IDX                           = 474,
    SBK_QLocale_IDX                                          = 192,
    SBK_QLocationPermission_Accuracy_IDX                     = 203,
    SBK_QLocationPermission_Availability_IDX                 = 204,
    SBK_QLocationPermission_IDX                              = 202,
    SBK_QLockFile_LockError_IDX                              = 206,
    SBK_QLockFile_IDX                                        = 205,
    SBK_QLoggingCategory_IDX                                 = 207,
    SBK_QMargins_IDX                                         = 208,
    SBK_QMarginsF_IDX                                        = 209,
    SBK_QMessageAuthenticationCode_IDX                       = 210,
    SBK_QMessageLogContext_IDX                               = 211,
    SBK_QMessageLogger_IDX                                   = 212,
    SBK_QMetaClassInfo_IDX                                   = 213,
    SBK_QMetaEnum_IDX                                        = 214,
    SBK_QMetaMethod_Access_IDX                               = 216,
    SBK_QMetaMethod_MethodType_IDX                           = 217,
    SBK_QMetaMethod_IDX                                      = 215,
    SBK_QMetaObject_Call_IDX                                 = 219,
    SBK_QMetaObject_IDX                                      = 218,
    SBK_QMetaObject_Connection_IDX                           = 220,
    SBK_QMetaProperty_IDX                                    = 221,
    SBK_QMetaType_Type_IDX                                   = 223,
    SBK_QMetaType_TypeFlag_IDX                               = 224,
    SBK_QFlags_QMetaType_TypeFlag_IDX                        = 126,
    SBK_QMetaType_IDX                                        = 222,
    SBK_QMicrophonePermission_IDX                            = 225,
    SBK_QMimeData_IDX                                        = 226,
    SBK_QMimeDatabase_MatchMode_IDX                          = 228,
    SBK_QMimeDatabase_IDX                                    = 227,
    SBK_QMimeType_IDX                                        = 229,
    SBK_QModelIndex_IDX                                      = 230,
    SBK_QModelRoleData_IDX                                   = 231,
    SBK_QModelRoleDataSpan_IDX                               = 232,
    SBK_QMutex_IDX                                           = 233,
    SBK_QNativeIpcKey_Type_IDX                               = 235,
    SBK_QNativeIpcKey_IDX                                    = 234,
    SBK_QObject_IDX                                          = 236,
    SBK_QOperatingSystemVersion_OSType_IDX                   = 238,
    SBK_QOperatingSystemVersion_IDX                          = 237,
    SBK_QOperatingSystemVersionBase_IDX                      = 239,
    SBK_QParallelAnimationGroup_IDX                          = 240,
    SBK_QPauseAnimation_IDX                                  = 241,
    SBK_QPermission_IDX                                      = 242,
    SBK_QPersistentModelIndex_IDX                            = 243,
    SBK_QPluginLoader_IDX                                    = 244,
    SBK_QPoint_IDX                                           = 245,
    SBK_QPointF_IDX                                          = 246,
    SBK_QProcess_ProcessError_IDX                            = 252,
    SBK_QProcess_ProcessState_IDX                            = 253,
    SBK_QProcess_ProcessChannel_IDX                          = 250,
    SBK_QProcess_ProcessChannelMode_IDX                      = 251,
    SBK_QProcess_InputChannelMode_IDX                        = 249,
    SBK_QProcess_ExitStatus_IDX                              = 248,
    SBK_QProcess_IDX                                         = 247,
    SBK_QProcessEnvironment_Initialization_IDX               = 255,
    SBK_QProcessEnvironment_IDX                              = 254,
    SBK_QPropertyAnimation_IDX                               = 256,
    SBK_QRandomGenerator_IDX                                 = 257,
    SBK_QRandomGenerator64_IDX                               = 258,
    SBK_QRangeModel_AutoConnectPolicy_IDX                    = 260,
    SBK_QRangeModel_RowCategory_IDX                          = 261,
    SBK_QRangeModel_IDX                                      = 259,
    SBK_QReadLocker_IDX                                      = 262,
    SBK_QReadWriteLock_RecursionMode_IDX                     = 264,
    SBK_QReadWriteLock_IDX                                   = 263,
    SBK_QRect_IDX                                            = 265,
    SBK_QRectF_IDX                                           = 266,
    SBK_QRecursiveMutex_IDX                                  = 267,
    SBK_QRegularExpression_PatternOption_IDX                 = 271,
    SBK_QFlags_QRegularExpression_PatternOption_IDX          = 128,
    SBK_QRegularExpression_MatchType_IDX                     = 270,
    SBK_QRegularExpression_MatchOption_IDX                   = 269,
    SBK_QFlags_QRegularExpression_MatchOption_IDX            = 127,
    SBK_QRegularExpression_WildcardConversionOption_IDX      = 272,
    SBK_QFlags_QRegularExpression_WildcardConversionOption_IDX = 129,
    SBK_QRegularExpression_IDX                               = 268,
    SBK_QRegularExpressionMatch_IDX                          = 273,
    SBK_QRegularExpressionMatchIterator_IDX                  = 274,
    SBK_QResource_Compression_IDX                            = 276,
    SBK_QResource_IDX                                        = 275,
    SBK_QRunnable_IDX                                        = 277,
    SBK_QSaveFile_IDX                                        = 278,
    SBK_QSemaphore_IDX                                       = 279,
    SBK_QSemaphoreReleaser_IDX                               = 280,
    SBK_QSequentialAnimationGroup_IDX                        = 281,
    SBK_QSettings_Status_IDX                                 = 285,
    SBK_QSettings_Format_IDX                                 = 283,
    SBK_QSettings_Scope_IDX                                  = 284,
    SBK_QSettings_IDX                                        = 282,
    SBK_QSharedMemory_AccessMode_IDX                         = 287,
    SBK_QSharedMemory_SharedMemoryError_IDX                  = 288,
    SBK_QSharedMemory_IDX                                    = 286,
    SBK_QSignalBlocker_IDX                                   = 289,
    SBK_QSignalMapper_IDX                                    = 290,
    SBK_QSize_IDX                                            = 291,
    SBK_QSizeF_IDX                                           = 292,
    SBK_QSocketDescriptor_IDX                                = 293,
    SBK_QSocketNotifier_Type_IDX                             = 295,
    SBK_QSocketNotifier_IDX                                  = 294,
    SBK_QSortFilterProxyModel_Direction_IDX                  = 297,
    SBK_QFlags_QSortFilterProxyModel_Direction_IDX           = 130,
    SBK_QSortFilterProxyModel_IDX                            = 296,
    SBK_QStandardPaths_StandardLocation_IDX                  = 300,
    SBK_QStandardPaths_LocateOption_IDX                      = 299,
    SBK_QFlags_QStandardPaths_LocateOption_IDX               = 131,
    SBK_QStandardPaths_IDX                                   = 298,
    SBK_QStorageInfo_IDX                                     = 301,
    SBK_QStringConverter_Encoding_IDX                        = 303,
    SBK_QStringConverter_IDX                                 = 302,
    SBK_QStringConverterBase_Flag_IDX                        = 305,
    SBK_QFlags_QStringConverterBase_Flag_IDX                 = 132,
    SBK_QStringConverterBase_IDX                             = 304,
    SBK_QStringConverterBase_State_IDX                       = 306,
    SBK_QStringDecoder_IDX                                   = 307,
    SBK_QStringEncoder_IDX                                   = 308,
    SBK_QStringListModel_IDX                                 = 309,
    SBK_QSysInfo_Sizes_IDX                                   = 312,
    SBK_QSysInfo_Endian_IDX                                  = 311,
    SBK_QSysInfo_IDX                                         = 310,
    SBK_QSystemSemaphore_AccessMode_IDX                      = 314,
    SBK_QSystemSemaphore_SystemSemaphoreError_IDX            = 315,
    SBK_QSystemSemaphore_IDX                                 = 313,
    SBK_QTemporaryDir_IDX                                    = 316,
    SBK_QTemporaryFile_IDX                                   = 317,
    SBK_QTextBoundaryFinder_BoundaryType_IDX                 = 320,
    SBK_QTextBoundaryFinder_BoundaryReason_IDX               = 319,
    SBK_QFlags_QTextBoundaryFinder_BoundaryReason_IDX        = 133,
    SBK_QTextBoundaryFinder_IDX                              = 318,
    SBK_QTextStream_RealNumberNotation_IDX                   = 324,
    SBK_QTextStream_FieldAlignment_IDX                       = 322,
    SBK_QTextStream_Status_IDX                               = 325,
    SBK_QTextStream_NumberFlag_IDX                           = 323,
    SBK_QFlags_QTextStream_NumberFlag_IDX                    = 134,
    SBK_QTextStream_IDX                                      = 321,
    SBK_QTextStreamManipulator_IDX                           = 326,
    SBK_QThread_Priority_IDX                                 = 328,
    SBK_QThread_QualityOfService_IDX                         = 329,
    SBK_QThread_IDX                                          = 327,
    SBK_QThreadPool_IDX                                      = 330,
    SBK_QTime_IDX                                            = 331,
    SBK_QTimeLine_State_IDX                                  = 334,
    SBK_QTimeLine_Direction_IDX                              = 333,
    SBK_QTimeLine_IDX                                        = 332,
    SBK_QTimeZone_Initialization_IDX                         = 336,
    SBK_QTimeZone_TimeType_IDX                               = 339,
    SBK_QTimeZone_NameType_IDX                               = 337,
    SBK_QTimeZone_IDX                                        = 335,
    SBK_QTimeZone_OffsetData_IDX                             = 338,
    SBK_QTimer_IDX                                           = 340,
    SBK_QTimerEvent_IDX                                      = 341,
    SBK_QTranslator_IDX                                      = 342,
    SBK_QTransposeProxyModel_IDX                             = 343,
    SBK_QUrl_ParsingMode_IDX                                 = 347,
    SBK_QUrl_UrlFormattingOption_IDX                         = 348,
    SBK_QUrl_ComponentFormattingOption_IDX                   = 346,
    SBK_QFlags_QUrl_ComponentFormattingOption_IDX            = 136,
    SBK_QUrl_UserInputResolutionOption_IDX                   = 349,
    SBK_QFlags_QUrl_UserInputResolutionOption_IDX            = 138,
    SBK_QUrl_AceProcessingOption_IDX                         = 345,
    SBK_QFlags_QUrl_AceProcessingOption_IDX                  = 135,
    SBK_QUrl_IDX                                             = 344,
    SBK_QUrlQuery_IDX                                        = 350,
    SBK_QUuid_Variant_IDX                                    = 353,
    SBK_QUuid_Version_IDX                                    = 354,
    SBK_QUuid_StringFormat_IDX                               = 352,
    SBK_QUuid_IDX                                            = 351,
    SBK_QVariantAnimation_IDX                                = 355,
    SBK_QVersionNumber_IDX                                   = 356,
    SBK_QWaitCondition_IDX                                   = 357,
    SBK_QWinEventNotifier_IDX                                = 358,
    SBK_QWriteLocker_IDX                                     = 359,
    SBK_QXmlStreamAttribute_IDX                              = 360,
    SBK_QXmlStreamAttributes_IDX                             = 361,
    SBK_QXmlStreamEntityDeclaration_IDX                      = 362,
    SBK_QXmlStreamEntityResolver_IDX                         = 363,
    SBK_QXmlStreamNamespaceDeclaration_IDX                   = 364,
    SBK_QXmlStreamNotationDeclaration_IDX                    = 365,
    SBK_QXmlStreamReader_TokenType_IDX                       = 369,
    SBK_QXmlStreamReader_ReadElementTextBehaviour_IDX        = 368,
    SBK_QXmlStreamReader_Error_IDX                           = 367,
    SBK_QXmlStreamReader_IDX                                 = 366,
    SBK_QXmlStreamWriter_Error_IDX                           = 371,
    SBK_QXmlStreamWriter_IDX                                 = 370,
    SBK_Qt_GlobalColor_IDX                                   = 409,
    SBK_Qt_ColorScheme_IDX                                   = 386,
    SBK_Qt_ContrastPreference_IDX                            = 390,
    SBK_Qt_MouseButton_IDX                                   = 425,
    SBK_QFlags_Qt_MouseButton_IDX                            = 152,
    SBK_Qt_Orientation_IDX                                   = 430,
    SBK_QFlags_Qt_Orientation_IDX                            = 154,
    SBK_Qt_FocusPolicy_IDX                                   = 404,
    SBK_Qt_TabFocusBehavior_IDX                              = 444,
    SBK_Qt_SortOrder_IDX                                     = 442,
    SBK_Qt_SplitBehaviorFlags_IDX                            = 443,
    SBK_QFlags_Qt_SplitBehaviorFlags_IDX                     = 156,
    SBK_Qt_TileRule_IDX                                      = 449,
    SBK_Qt_AlignmentFlag_IDX                                 = 373,
    SBK_QFlags_Qt_AlignmentFlag_IDX                          = 139,
    SBK_Qt_TextFlag_IDX                                      = 446,
    SBK_Qt_TextElideMode_IDX                                 = 445,
    SBK_Qt_WhiteSpaceMode_IDX                                = 459,
    SBK_Qt_HitTestAccuracy_IDX                               = 411,
    SBK_Qt_WindowType_IDX                                    = 464,
    SBK_QFlags_Qt_WindowType_IDX                             = 161,
    SBK_Qt_WindowState_IDX                                   = 463,
    SBK_QFlags_Qt_WindowState_IDX                            = 160,
    SBK_Qt_ApplicationState_IDX                              = 376,
    SBK_QFlags_Qt_ApplicationState_IDX                       = 140,
    SBK_Qt_ScreenOrientation_IDX                             = 436,
    SBK_QFlags_Qt_ScreenOrientation_IDX                      = 155,
    SBK_Qt_WidgetAttribute_IDX                               = 460,
    SBK_Qt_ApplicationAttribute_IDX                          = 375,
    SBK_Qt_ImageConversionFlag_IDX                           = 412,
    SBK_QFlags_Qt_ImageConversionFlag_IDX                    = 146,
    SBK_Qt_BGMode_IDX                                        = 380,
    SBK_Qt_Key_IDX                                           = 419,
    SBK_Qt_KeyboardModifier_IDX                              = 420,
    SBK_QFlags_Qt_KeyboardModifier_IDX                       = 150,
    SBK_Qt_Modifier_IDX                                      = 424,
    SBK_Qt_ArrowType_IDX                                     = 377,
    SBK_Qt_PenStyle_IDX                                      = 433,
    SBK_Qt_PenCapStyle_IDX                                   = 431,
    SBK_Qt_PenJoinStyle_IDX                                  = 432,
    SBK_Qt_BrushStyle_IDX                                    = 381,
    SBK_Qt_SizeMode_IDX                                      = 441,
    SBK_Qt_UIEffect_IDX                                      = 458,
    SBK_Qt_CursorShape_IDX                                   = 393,
    SBK_Qt_TextFormat_IDX                                    = 447,
    SBK_Qt_AspectRatioMode_IDX                               = 378,
    SBK_Qt_DockWidgetArea_IDX                                = 396,
    SBK_QFlags_Qt_DockWidgetArea_IDX                         = 141,
    SBK_Qt_DockWidgetAreaSizes_IDX                           = 397,
    SBK_Qt_ToolBarArea_IDX                                   = 453,
    SBK_QFlags_Qt_ToolBarArea_IDX                            = 158,
    SBK_Qt_ToolBarAreaSizes_IDX                              = 454,
    SBK_Qt_DateFormat_IDX                                    = 394,
    SBK_Qt_TimeSpec_IDX                                      = 450,
    SBK_Qt_DayOfWeek_IDX                                     = 395,
    SBK_Qt_ScrollBarPolicy_IDX                               = 437,
    SBK_Qt_CaseSensitivity_IDX                               = 382,
    SBK_Qt_Corner_IDX                                        = 392,
    SBK_Qt_Edge_IDX                                          = 399,
    SBK_QFlags_Qt_Edge_IDX                                   = 143,
    SBK_Qt_ConnectionType_IDX                                = 387,
    SBK_Qt_ShortcutContext_IDX                               = 439,
    SBK_Qt_FillRule_IDX                                      = 402,
    SBK_Qt_MaskMode_IDX                                      = 422,
    SBK_Qt_ClipOperation_IDX                                 = 385,
    SBK_Qt_ItemSelectionMode_IDX                             = 417,
    SBK_Qt_ItemSelectionOperation_IDX                        = 418,
    SBK_Qt_TransformationMode_IDX                            = 457,
    SBK_Qt_Axis_IDX                                          = 379,
    SBK_Qt_FocusReason_IDX                                   = 405,
    SBK_Qt_ContextMenuPolicy_IDX                             = 388,
    SBK_Qt_ContextMenuTrigger_IDX                            = 389,
    SBK_Qt_InputMethodQuery_IDX                              = 414,
    SBK_QFlags_Qt_InputMethodQuery_IDX                       = 148,
    SBK_Qt_InputMethodHint_IDX                               = 413,
    SBK_QFlags_Qt_InputMethodHint_IDX                        = 147,
    SBK_Qt_EnterKeyType_IDX                                  = 400,
    SBK_Qt_ToolButtonStyle_IDX                               = 455,
    SBK_Qt_LayoutDirection_IDX                               = 421,
    SBK_Qt_AnchorPoint_IDX                                   = 374,
    SBK_Qt_FindChildOption_IDX                               = 403,
    SBK_QFlags_Qt_FindChildOption_IDX                        = 144,
    SBK_Qt_DropAction_IDX                                    = 398,
    SBK_QFlags_Qt_DropAction_IDX                             = 142,
    SBK_Qt_CheckState_IDX                                    = 383,
    SBK_Qt_ItemDataRole_IDX                                  = 415,
    SBK_Qt_ItemFlag_IDX                                      = 416,
    SBK_QFlags_Qt_ItemFlag_IDX                               = 149,
    SBK_Qt_MatchFlag_IDX                                     = 423,
    SBK_QFlags_Qt_MatchFlag_IDX                              = 151,
    SBK_Qt_WindowModality_IDX                                = 462,
    SBK_Qt_TextInteractionFlag_IDX                           = 448,
    SBK_QFlags_Qt_TextInteractionFlag_IDX                    = 157,
    SBK_Qt_EventPriority_IDX                                 = 401,
    SBK_Qt_SizeHint_IDX                                      = 440,
    SBK_Qt_WindowFrameSection_IDX                            = 461,
    SBK_Qt_CoordinateSystem_IDX                              = 391,
    SBK_Qt_TouchPointState_IDX                               = 456,
    SBK_QFlags_Qt_TouchPointState_IDX                        = 159,
    SBK_Qt_GestureState_IDX                                  = 407,
    SBK_Qt_GestureType_IDX                                   = 408,
    SBK_Qt_GestureFlag_IDX                                   = 406,
    SBK_QFlags_Qt_GestureFlag_IDX                            = 145,
    SBK_Qt_NativeGestureType_IDX                             = 428,
    SBK_Qt_NavigationMode_IDX                                = 429,
    SBK_Qt_CursorMoveStyle_IDX                               = 476,
    SBK_Qt_TimerType_IDX                                     = 452,
    SBK_Qt_TimerId_IDX                                       = 451,
    SBK_Qt_ScrollPhase_IDX                                   = 438,
    SBK_Qt_MouseEventSource_IDX                              = 427,
    SBK_Qt_MouseEventFlag_IDX                                = 426,
    SBK_QFlags_Qt_MouseEventFlag_IDX                         = 153,
    SBK_Qt_ChecksumType_IDX                                  = 384,
    SBK_Qt_HighDpiScaleFactorRoundingPolicy_IDX              = 410,
    SBK_Qt_PermissionStatus_IDX                              = 434,
    SBK_Qt_ReturnByValueConstant_IDX                         = 435,
    SBK_QtCoreQt_IDX                                         = 372,
    SBK_QtCoreHelper_QDirListingIterator_IDX                 = 466,
    SBK_QtCoreHelper_QGenericArgumentHolder_IDX              = 467,
    SBK_QtCoreHelper_QGenericReturnArgumentHolder_IDX        = 468,
    SBK_QtCoreHelper_QIOPipe_IDX                             = 469,
    SBK_QtCoreHelper_QMutexLocker_IDX                        = 470,
    SBK_QCborKnownTags_IDX                                   = 37,
    SBK_QCborSimpleType_IDX                                  = 40,
    SBK_QCborTag_IDX                                         = 47,
    SBK_QtMsgType_IDX                                        = 471,
    SBK_QtCore_IDX_COUNT                                     = 477,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtCoreTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtCoreModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtCoreTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    // SBK_HWND_IDX                                          = 0,
    SBK_QANYSTRINGVIEW_IDX                                   = 1,
    SBK_QBYTEARRAYVIEW_IDX                                   = 2,
    SBK_QCHAR_IDX                                            = 3,
    SBK_QFUNCTIONPOINTER_IDX                                 = 4,
    SBK_QJSONOBJECT_IDX                                      = 5,
    SBK_QLATIN1STRING_IDX                                    = 6,
    SBK_QSTRING_IDX                                          = 7,
    SBK_QSTRINGLIST_IDX                                      = 8,
    SBK_QSTRINGVIEW_IDX                                      = 9,
    SBK_QVARIANT_IDX                                         = 10,
    SBK_QINTPTR_IDX                                          = 11,
    SBK_QPTRDIFF_IDX                                         = 12,
    SBK_QUINTPTR_IDX                                         = 13,
    SBK_STD_CHRONO_MILLISECONDS_IDX                          = 14,
    SBK_STD_CHRONO_SECONDS_IDX                               = 15,
    SBK_QTCORE_QLIST_INT_IDX                                 = 16, // QList<int>
    SBK_QTCORE_QLIST_QPOINT_IDX                              = 17, // QList<QPoint>
    SBK_QTCORE_QLIST_QPOINTF_IDX                             = 18, // QList<QPointF>
    SBK_QTCORE_QLIST_QXMLSTREAMNAMESPACEDECLARATION_IDX      = 19, // QList<QXmlStreamNamespaceDeclaration>
    SBK_QTCORE_QLIST_QXMLSTREAMENTITYDECLARATION_IDX         = 20, // QList<QXmlStreamEntityDeclaration>
    SBK_QTCORE_QLIST_QXMLSTREAMNOTATIONDECLARATION_IDX       = 21, // QList<QXmlStreamNotationDeclaration>
    SBK_QTCORE_QLIST_QXMLSTREAMATTRIBUTE_IDX                 = 22, // QList<QXmlStreamAttribute>
    SBK_QTCORE_STD_PAIR_QSTRING_QSTRING_IDX                  = 23, // std::pair<QString,QString>
    SBK_QTCORE_QLIST_STD_PAIR_QSTRING_QSTRING_IDX            = 24, // QList<std::pair<QString,QString>>
    SBK_QTCORE_QLIST_QSTORAGEINFO_IDX                        = 25, // QList<QStorageInfo>
    SBK_QTCORE_QLIST_QMIMETYPE_IDX                           = 26, // QList<QMimeType>
    SBK_QTCORE_QLIST_QLOCALE_COUNTRY_IDX                     = 27, // QList<QLocale::Country>
    SBK_QTCORE_QLIST_QLOCALE_IDX                             = 28, // QList<QLocale>
    SBK_QTCORE_QLIST_QT_DAYOFWEEK_IDX                        = 29, // QList<Qt::DayOfWeek>
    SBK_QTCORE_QLIST_QBYTEARRAY_IDX                          = 30, // QList<QByteArray>
    SBK_QTCORE_QLIST_QTIMEZONE_OFFSETDATA_IDX                = 31, // QList<QTimeZone::OffsetData>
    SBK_QTCORE_QLIST_QVARIANT_IDX                            = 32, // QList<QVariant>
    SBK_QTCORE_QLIST_QJSONOBJECT_IDX                         = 33, // QList<QJsonObject>
    SBK_QTCORE_QLIST_QMODELINDEX_IDX                         = 34, // QList<QModelIndex>
    SBK_QTCORE_QLIST_QITEMSELECTIONRANGE_IDX                 = 35, // QList<QItemSelectionRange>
    SBK_QTCORE_QLIST_QOBJECTPTR_IDX                          = 36, // QList<QObject*>
    SBK_QTCORE_QLIST_QURL_IDX                                = 37, // QList<QUrl>
    SBK_QTCORE_QLIST_QFILEINFO_IDX                           = 38, // QList<QFileInfo>
    SBK_QTCORE_QLIST_QCOMMANDLINEOPTION_IDX                  = 39, // QList<QCommandLineOption>
    SBK_QTCORE_QHASH_QSTRING_QVARIANT_IDX                    = 40, // QHash<QString,QVariant>
    SBK_QTCORE_QMAP_QSTRING_QVARIANT_IDX                     = 41, // QMap<QString,QVariant>
    SBK_QTCORE_QLIST_QCBORVALUE_IDX                          = 42, // QList<QCborValue>
    SBK_QTCORE_QMAP_INT_QVARIANT_IDX                         = 43, // QMap<int,QVariant>
    SBK_QTCORE_QLIST_QPERSISTENTMODELINDEX_IDX               = 44, // QList<QPersistentModelIndex>
    SBK_QTCORE_QHASH_INT_QBYTEARRAY_IDX                      = 45, // QHash<int,QByteArray>
    SBK_QTCORE_QLIST_QABSTRACTITEMMODELPTR_IDX               = 46, // QList<QAbstractItemModel*>
    SBK_QTCORE_QLIST_QABSTRACTEVENTDISPATCHER_TIMERINFO_IDX  = 47, // QList<QAbstractEventDispatcher::TimerInfo>
    SBK_QTCORE_STD_PAIR_DOUBLE_QVARIANT_IDX                  = 48, // std::pair<double,QVariant>
    SBK_QTCORE_QLIST_STD_PAIR_DOUBLE_QVARIANT_IDX            = 49, // QList<std::pair<double,QVariant>>
    SBK_QTCORE_QLIST_QSTRING_IDX                             = 50, // QList<QString>
    SBK_QTCORE_CONVERTERS_IDX_COUNT                          = 51,
};

// Converter indices
enum : int {
    SBK_HWND_IDX                                             = 0,
    SBK_QAnyStringView_IDX                                   = 1,
    SBK_QByteArrayView_IDX                                   = 2,
    SBK_QChar_IDX                                            = 3,
    SBK_QFunctionPointer_IDX                                 = 4,
    SBK_QJsonObject_IDX                                      = 5,
    SBK_QLatin1String_IDX                                    = 6,
    SBK_QString_IDX                                          = 7,
    SBK_QStringList_IDX                                      = 8,
    SBK_QStringView_IDX                                      = 9,
    SBK_QVariant_IDX                                         = 10,
    SBK_qintptr_IDX                                          = 11,
    SBK_qptrdiff_IDX                                         = 12,
    SBK_quintptr_IDX                                         = 13,
    SBK_std_chrono_milliseconds_IDX                          = 14,
    SBK_std_chrono_seconds_IDX                               = 15,
    SBK_QtCore_QList_int_IDX                                 = 16, // QList<int>
    SBK_QtCore_QList_QPoint_IDX                              = 17, // QList<QPoint>
    SBK_QtCore_QList_QPointF_IDX                             = 18, // QList<QPointF>
    SBK_QtCore_QList_QXmlStreamNamespaceDeclaration_IDX      = 19, // QList<QXmlStreamNamespaceDeclaration>
    SBK_QtCore_QList_QXmlStreamEntityDeclaration_IDX         = 20, // QList<QXmlStreamEntityDeclaration>
    SBK_QtCore_QList_QXmlStreamNotationDeclaration_IDX       = 21, // QList<QXmlStreamNotationDeclaration>
    SBK_QtCore_QList_QXmlStreamAttribute_IDX                 = 22, // QList<QXmlStreamAttribute>
    SBK_QtCore_std_pair_QString_QString_IDX                  = 23, // std::pair<QString,QString>
    SBK_QtCore_QList_std_pair_QString_QString_IDX            = 24, // QList<std::pair<QString,QString>>
    SBK_QtCore_QList_QStorageInfo_IDX                        = 25, // QList<QStorageInfo>
    SBK_QtCore_QList_QMimeType_IDX                           = 26, // QList<QMimeType>
    SBK_QtCore_QList_QLocale_Country_IDX                     = 27, // QList<QLocale::Country>
    SBK_QtCore_QList_QLocale_IDX                             = 28, // QList<QLocale>
    SBK_QtCore_QList_Qt_DayOfWeek_IDX                        = 29, // QList<Qt::DayOfWeek>
    SBK_QtCore_QList_QByteArray_IDX                          = 30, // QList<QByteArray>
    SBK_QtCore_QList_QTimeZone_OffsetData_IDX                = 31, // QList<QTimeZone::OffsetData>
    SBK_QtCore_QList_QVariant_IDX                            = 32, // QList<QVariant>
    SBK_QtCore_QList_QJsonObject_IDX                         = 33, // QList<QJsonObject>
    SBK_QtCore_QList_QModelIndex_IDX                         = 34, // QList<QModelIndex>
    SBK_QtCore_QList_QItemSelectionRange_IDX                 = 35, // QList<QItemSelectionRange>
    SBK_QtCore_QList_QObjectPTR_IDX                          = 36, // QList<QObject*>
    SBK_QtCore_QList_QUrl_IDX                                = 37, // QList<QUrl>
    SBK_QtCore_QList_QFileInfo_IDX                           = 38, // QList<QFileInfo>
    SBK_QtCore_QList_QCommandLineOption_IDX                  = 39, // QList<QCommandLineOption>
    SBK_QtCore_QHash_QString_QVariant_IDX                    = 40, // QHash<QString,QVariant>
    SBK_QtCore_QMap_QString_QVariant_IDX                     = 41, // QMap<QString,QVariant>
    SBK_QtCore_QList_QCborValue_IDX                          = 42, // QList<QCborValue>
    SBK_QtCore_QMap_int_QVariant_IDX                         = 43, // QMap<int,QVariant>
    SBK_QtCore_QList_QPersistentModelIndex_IDX               = 44, // QList<QPersistentModelIndex>
    SBK_QtCore_QHash_int_QByteArray_IDX                      = 45, // QHash<int,QByteArray>
    SBK_QtCore_QList_QAbstractItemModelPTR_IDX               = 46, // QList<QAbstractItemModel*>
    SBK_QtCore_QList_QAbstractEventDispatcher_TimerInfo_IDX  = 47, // QList<QAbstractEventDispatcher::TimerInfo>
    SBK_QtCore_std_pair_double_QVariant_IDX                  = 48, // std::pair<double,QVariant>
    SBK_QtCore_QList_std_pair_double_QVariant_IDX            = 49, // QList<std::pair<double,QVariant>>
    SBK_QtCore_QList_QString_IDX                             = 50, // QList<QString>
    SBK_QtCore_CONVERTERS_IDX_COUNT                          = 51,
};

// typedef entries
using QCborStringResultByteArray = QCborStreamReader::StringResult<QByteArray>;
using QCborStringResultString = QCborStreamReader::StringResult<QString>;

// Macros for type check

// Protected enum surrogates
enum PySide6_QtCore_QFutureInterfaceBase_ContinuationType_Surrogate : unsigned char {};
enum PySide6_QtCore_QFutureInterfaceBase_CancelMode_Surrogate : int {};

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QCborKnownTags >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborKnownTags_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborSimpleType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborSimpleType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborTag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborTag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtMsgType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QtMsgType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractAnimation::Direction >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractAnimation_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractAnimation::State >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractAnimation_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractAnimation::DeletionPolicy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractAnimation_DeletionPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractAnimation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractAnimation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractEventDispatcher >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractEventDispatcher_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractEventDispatcher::TimerInfo >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractEventDispatcher_TimerInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemModel::LayoutChangeHint >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractItemModel_LayoutChangeHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemModel::CheckIndexOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractItemModel_CheckIndexOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QAbstractItemModel::CheckIndexOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QAbstractItemModel_CheckIndexOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractItemModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractListModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractListModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractNativeEventFilter >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractNativeEventFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractProxyModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractProxyModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractTableModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAbstractTableModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAnimationGroup >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QAnimationGroup_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QBasicMutex >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QBasicMutex_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QBasicReadWriteLock >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QBasicReadWriteLock_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBasicTimer >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QBasicTimer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBitArray >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QBitArray_IDX]); }
#if QT_CONFIG(permissions)
template<> inline PyTypeObject *SbkType< ::QBluetoothPermission::CommunicationMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QBluetoothPermission_CommunicationMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QBluetoothPermission::CommunicationMode> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QBluetoothPermission_CommunicationMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBluetoothPermission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QBluetoothPermission_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QBuffer >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QBuffer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QByteArray::Base64Option >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QByteArray_Base64Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QByteArray::Base64Option> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QByteArray_Base64Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QByteArray::Base64DecodingStatus >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QByteArray_Base64DecodingStatus_IDX]); }
template<> inline PyTypeObject *SbkType< ::QByteArray >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QByteArray_IDX]); }
template<> inline PyTypeObject *SbkType< ::QByteArray::FromBase64Result >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QByteArray_FromBase64Result_IDX]); }
template<> inline PyTypeObject *SbkType< ::QByteArrayMatcher >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QByteArrayMatcher_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendar::System >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCalendar_System_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendar >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCalendar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendar::SystemId >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCalendar_SystemId_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendar::YearMonthDay >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCalendar_YearMonthDay_IDX]); }
#if QT_CONFIG(permissions)
template<> inline PyTypeObject *SbkType< ::QCalendarPermission::AccessMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCalendarPermission_AccessMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendarPermission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCalendarPermission_IDX]); }
#endif
#if QT_CONFIG(permissions)
template<> inline PyTypeObject *SbkType< ::QCameraPermission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCameraPermission_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QCborArray >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborArray_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborError::Code >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborError_Code_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborMap >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborMap_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborParserError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborParserError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborStreamReader::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborStreamReader_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborStreamReader::StringResultCode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborStreamReader_StringResultCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborStreamReader >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborStreamReader_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborStreamWriter >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborStreamWriter_IDX]); }
template<> inline PyTypeObject *SbkType< QCborStringResultByteArray >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborStringResultByteArray_IDX]); }
template<> inline PyTypeObject *SbkType< QCborStringResultString >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborStringResultString_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborValue::EncodingOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborValue_EncodingOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCborValue::EncodingOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QCborValue_EncodingOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborValue::DiagnosticNotationOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborValue_DiagnosticNotationOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCborValue::DiagnosticNotationOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QCborValue_DiagnosticNotationOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborValue::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborValue_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCborValue >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCborValue_IDX]); }
template<> inline PyTypeObject *SbkType< ::QChildEvent >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QChildEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCollator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCollator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCollatorSortKey >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCollatorSortKey_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommandLineOption::Flag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCommandLineOption_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QCommandLineOption::Flag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QCommandLineOption_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommandLineOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCommandLineOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommandLineParser::SingleDashWordOptionMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCommandLineParser_SingleDashWordOptionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommandLineParser::OptionsAfterPositionalArgumentsMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCommandLineParser_OptionsAfterPositionalArgumentsMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommandLineParser::MessageType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCommandLineParser_MessageType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommandLineParser >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCommandLineParser_IDX]); }
template<> inline PyTypeObject *SbkType< ::QConcatenateTablesProxyModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QConcatenateTablesProxyModel_IDX]); }
#if QT_CONFIG(permissions)
template<> inline PyTypeObject *SbkType< ::QContactsPermission::AccessMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QContactsPermission_AccessMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QContactsPermission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QContactsPermission_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QCoreApplication >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCoreApplication_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCryptographicHash::Algorithm >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCryptographicHash_Algorithm_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCryptographicHash >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QCryptographicHash_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDataStream::Version >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDataStream_Version_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDataStream::ByteOrder >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDataStream_ByteOrder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDataStream::Status >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDataStream_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDataStream::FloatingPointPrecision >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDataStream_FloatingPointPrecision_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDataStream >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDataStream_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDate >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDate_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDateTime::TransitionResolution >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDateTime_TransitionResolution_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDateTime::YearRange >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDateTime_YearRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDateTime >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDateTime_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDeadlineTimer::ForeverConstant >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDeadlineTimer_ForeverConstant_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDeadlineTimer >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDeadlineTimer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDir::Filter >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDir_Filter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QDir::Filter> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QDir_Filter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDir::SortFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDir_SortFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QDir::SortFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QDir_SortFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDir >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDir_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDirIterator::IteratorFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDirIterator_IteratorFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QDirIterator::IteratorFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QDirIterator_IteratorFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDirIterator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDirIterator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDirListing::IteratorFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDirListing_IteratorFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QDirListing::IteratorFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QDirListing_IteratorFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDirListing >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDirListing_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDirListing::DirEntry >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDirListing_DirEntry_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDynamicPropertyChangeEvent >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QDynamicPropertyChangeEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QEasingCurve::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QEasingCurve_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QEasingCurve >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QEasingCurve_IDX]); }
template<> inline PyTypeObject *SbkType< ::QElapsedTimer::ClockType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QElapsedTimer_ClockType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QElapsedTimer >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QElapsedTimer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QEvent::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QEvent_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QEvent >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QEventLoop::ProcessEventsFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QEventLoop_ProcessEventsFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QEventLoop::ProcessEventsFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QEventLoop_ProcessEventsFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QEventLoop >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QEventLoop_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFactoryInterface >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFactoryInterface_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFile >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFile_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDevice::FileError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileDevice_FileError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDevice::FileTime >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileDevice_FileTime_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDevice::Permission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileDevice_Permission_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QFileDevice::Permission> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QFileDevice_Permission_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDevice::FileHandleFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileDevice_FileHandleFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QFileDevice::FileHandleFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QFileDevice_FileHandleFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDevice::MemoryMapFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileDevice_MemoryMapFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QFileDevice::MemoryMapFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QFileDevice_MemoryMapFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDevice >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileDevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileInfo >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileSelector >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileSelector_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileSystemWatcher >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFileSystemWatcher_IDX]); }
#if QT_CONFIG(future)
template<> inline PyTypeObject *SbkType< ::QFutureInterfaceBase::State >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFutureInterfaceBase_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtCore_QFutureInterfaceBase_ContinuationType_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFutureInterfaceBase_ContinuationType_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtCore_QFutureInterfaceBase_CancelMode_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFutureInterfaceBase_CancelMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFutureInterfaceBase >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFutureInterfaceBase_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QGenericArgument >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QGenericArgument_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGenericReturnArgument >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QGenericReturnArgument_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHashSeed >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QHashSeed_IDX]); }
template<> inline PyTypeObject *SbkType< ::QIODevice >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QIODevice_IDX]); }
template<> inline PyTypeObject *SbkType< ::QIODeviceBase::OpenModeFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QIODeviceBase_OpenModeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QIODeviceBase::OpenModeFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QIODeviceBase_OpenModeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QIODeviceBase >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QIODeviceBase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QIdentityProxyModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QIdentityProxyModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemSelection >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QItemSelection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemSelectionModel::SelectionFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QItemSelectionModel_SelectionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QItemSelectionModel::SelectionFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QItemSelectionModel_SelectionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemSelectionModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QItemSelectionModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemSelectionRange >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QItemSelectionRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QJsonArray >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QJsonArray_IDX]); }
template<> inline PyTypeObject *SbkType< ::QJsonDocument::JsonFormat >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QJsonDocument_JsonFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QJsonDocument >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QJsonDocument_IDX]); }
template<> inline PyTypeObject *SbkType< ::QJsonParseError::ParseError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QJsonParseError_ParseError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QJsonParseError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QJsonParseError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QJsonValue::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QJsonValue_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QJsonValue >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QJsonValue_IDX]); }
template<> inline PyTypeObject *SbkType< ::QKeyCombination >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QKeyCombination_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLibrary::LoadHint >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLibrary_LoadHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QLibrary::LoadHint> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QLibrary_LoadHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLibrary >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLibrary_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLibraryInfo::LibraryPath >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLibraryInfo_LibraryPath_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLibraryInfo >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLibraryInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLine >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLine_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineF::IntersectionType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLineF_IntersectionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineF >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLineF_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::Language >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_Language_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::Script >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_Script_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::Country >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_Country_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::MeasurementSystem >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_MeasurementSystem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::FormatType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_FormatType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::NumberOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_NumberOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QLocale::NumberOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QLocale_NumberOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::FloatingPointPrecisionOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_FloatingPointPrecisionOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::TagSeparator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_TagSeparator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::CurrencySymbolFormat >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_CurrencySymbolFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::DataSizeFormat >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_DataSizeFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QLocale::DataSizeFormat> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QLocale_DataSizeFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::LanguageCodeType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_LanguageCodeType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QLocale::LanguageCodeType> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QLocale_LanguageCodeType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale::QuotationStyle >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_QuotationStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocale >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocale_IDX]); }
#if QT_CONFIG(permissions)
template<> inline PyTypeObject *SbkType< ::QLocationPermission::Accuracy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocationPermission_Accuracy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocationPermission::Availability >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocationPermission_Availability_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLocationPermission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLocationPermission_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QLockFile::LockError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLockFile_LockError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLockFile >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLockFile_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLoggingCategory >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QLoggingCategory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMargins >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMargins_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMarginsF >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMarginsF_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageAuthenticationCode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMessageAuthenticationCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageLogContext >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMessageLogContext_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageLogger >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMessageLogger_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaClassInfo >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaClassInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaEnum >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaEnum_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaMethod::Access >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaMethod_Access_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaMethod::MethodType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaMethod_MethodType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaMethod >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaObject::Call >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaObject_Call_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaObject >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaObject_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaObject::Connection >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaObject_Connection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaProperty >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaProperty_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaType::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaType_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaType::TypeFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaType_TypeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QMetaType::TypeFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QMetaType_TypeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMetaType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMetaType_IDX]); }
#if QT_CONFIG(permissions)
template<> inline PyTypeObject *SbkType< ::QMicrophonePermission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMicrophonePermission_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QMimeData >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMimeData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMimeDatabase::MatchMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMimeDatabase_MatchMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMimeDatabase >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMimeDatabase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMimeType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMimeType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModelIndex >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QModelIndex_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModelRoleData >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QModelRoleData_IDX]); }
template<> inline PyTypeObject *SbkType< ::QModelRoleDataSpan >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QModelRoleDataSpan_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QMutex >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QMutex_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QNativeIpcKey::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QNativeIpcKey_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QNativeIpcKey >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QNativeIpcKey_IDX]); }
template<> inline PyTypeObject *SbkType< ::QObject >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QObject_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOperatingSystemVersion::OSType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QOperatingSystemVersion_OSType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOperatingSystemVersion >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QOperatingSystemVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QOperatingSystemVersionBase >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QOperatingSystemVersionBase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QParallelAnimationGroup >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QParallelAnimationGroup_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPauseAnimation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QPauseAnimation_IDX]); }
#if QT_CONFIG(permissions)
template<> inline PyTypeObject *SbkType< ::QPermission >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QPermission_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QPersistentModelIndex >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QPersistentModelIndex_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPluginLoader >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QPluginLoader_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPoint >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QPoint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPointF >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QPointF_IDX]); }
#if QT_CONFIG(process)
template<> inline PyTypeObject *SbkType< ::QProcess::ProcessError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcess_ProcessError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProcess::ProcessState >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcess_ProcessState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProcess::ProcessChannel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcess_ProcessChannel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProcess::ProcessChannelMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcess_ProcessChannelMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProcess::InputChannelMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcess_InputChannelMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProcess::ExitStatus >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcess_ExitStatus_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProcess >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcess_IDX]); }
#endif
#if QT_CONFIG(processenvironment)
template<> inline PyTypeObject *SbkType< ::QProcessEnvironment::Initialization >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcessEnvironment_Initialization_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProcessEnvironment >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QProcessEnvironment_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QPropertyAnimation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QPropertyAnimation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRandomGenerator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRandomGenerator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRandomGenerator64 >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRandomGenerator64_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRangeModel::AutoConnectPolicy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRangeModel_AutoConnectPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRangeModel::RowCategory >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRangeModel_RowCategory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRangeModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRangeModel_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QReadLocker >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QReadLocker_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QReadWriteLock::RecursionMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QReadWriteLock_RecursionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QReadWriteLock >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QReadWriteLock_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRect >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRectF >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRectF_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QRecursiveMutex >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRecursiveMutex_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QRegularExpression::PatternOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRegularExpression_PatternOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QRegularExpression::PatternOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QRegularExpression_PatternOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRegularExpression::MatchType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRegularExpression_MatchType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRegularExpression::MatchOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRegularExpression_MatchOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QRegularExpression::MatchOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QRegularExpression_MatchOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRegularExpression::WildcardConversionOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRegularExpression_WildcardConversionOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QRegularExpression::WildcardConversionOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QRegularExpression_WildcardConversionOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRegularExpression >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRegularExpression_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRegularExpressionMatch >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRegularExpressionMatch_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRegularExpressionMatchIterator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRegularExpressionMatchIterator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QResource::Compression >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QResource_Compression_IDX]); }
template<> inline PyTypeObject *SbkType< ::QResource >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QResource_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QRunnable >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QRunnable_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QSaveFile >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSaveFile_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QSemaphore >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSemaphore_IDX]); }
#endif
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QSemaphoreReleaser >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSemaphoreReleaser_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QSequentialAnimationGroup >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSequentialAnimationGroup_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSettings::Status >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSettings_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSettings::Format >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSettings_Format_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSettings::Scope >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSettings_Scope_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSettings >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSettings_IDX]); }
#if QT_CONFIG(sharedmemory)
template<> inline PyTypeObject *SbkType< ::QSharedMemory::AccessMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSharedMemory_AccessMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSharedMemory::SharedMemoryError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSharedMemory_SharedMemoryError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSharedMemory >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSharedMemory_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QSignalBlocker >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSignalBlocker_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSignalMapper >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSignalMapper_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSize >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSize_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSizeF >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSizeF_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSocketDescriptor >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSocketDescriptor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSocketNotifier::Type >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSocketNotifier_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSocketNotifier >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSocketNotifier_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSortFilterProxyModel::Direction >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSortFilterProxyModel_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QSortFilterProxyModel::Direction> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QSortFilterProxyModel_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSortFilterProxyModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSortFilterProxyModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStandardPaths::StandardLocation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStandardPaths_StandardLocation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStandardPaths::LocateOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStandardPaths_LocateOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStandardPaths::LocateOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QStandardPaths_LocateOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStandardPaths >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStandardPaths_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStorageInfo >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStorageInfo_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringConverter::Encoding >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringConverter_Encoding_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringConverter >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringConverter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringConverterBase::Flag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringConverterBase_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStringConverterBase::Flag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QStringConverterBase_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringConverterBase >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringConverterBase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringConverterBase::State >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringConverterBase_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringDecoder >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringDecoder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringEncoder >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringEncoder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStringListModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QStringListModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSysInfo::Sizes >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSysInfo_Sizes_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSysInfo::Endian >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSysInfo_Endian_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSysInfo >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSysInfo_IDX]); }
#if QT_CONFIG(systemsemaphore)
template<> inline PyTypeObject *SbkType< ::QSystemSemaphore::AccessMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSystemSemaphore_AccessMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSystemSemaphore::SystemSemaphoreError >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSystemSemaphore_SystemSemaphoreError_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSystemSemaphore >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QSystemSemaphore_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QTemporaryDir >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTemporaryDir_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTemporaryFile >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTemporaryFile_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextBoundaryFinder::BoundaryType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextBoundaryFinder_BoundaryType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextBoundaryFinder::BoundaryReason >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextBoundaryFinder_BoundaryReason_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QTextBoundaryFinder::BoundaryReason> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QTextBoundaryFinder_BoundaryReason_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextBoundaryFinder >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextBoundaryFinder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextStream::RealNumberNotation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextStream_RealNumberNotation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextStream::FieldAlignment >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextStream_FieldAlignment_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextStream::Status >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextStream_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextStream::NumberFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextStream_NumberFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QTextStream::NumberFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QTextStream_NumberFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextStream >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextStream_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextStreamManipulator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTextStreamManipulator_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QThread::Priority >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QThread_Priority_IDX]); }
template<> inline PyTypeObject *SbkType< ::QThread::QualityOfService >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QThread_QualityOfService_IDX]); }
template<> inline PyTypeObject *SbkType< ::QThread >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QThread_IDX]); }
#endif
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QThreadPool >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QThreadPool_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QTime >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTime_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimeLine::State >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeLine_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimeLine::Direction >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeLine_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimeLine >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeLine_IDX]); }
#if QT_CONFIG(timezone)
template<> inline PyTypeObject *SbkType< ::QTimeZone::Initialization >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeZone_Initialization_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimeZone::TimeType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeZone_TimeType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimeZone::NameType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeZone_NameType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimeZone >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeZone_IDX]); }
#endif
#if QT_CONFIG(timezone)
template<> inline PyTypeObject *SbkType< ::QTimeZone::OffsetData >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimeZone_OffsetData_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QTimer >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimerEvent >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTimerEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTranslator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTranslator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTransposeProxyModel >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QTransposeProxyModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUrl::ParsingMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUrl_ParsingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUrl::UrlFormattingOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUrl_UrlFormattingOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUrl::ComponentFormattingOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUrl_ComponentFormattingOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QUrl::ComponentFormattingOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QUrl_ComponentFormattingOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUrl::UserInputResolutionOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUrl_UserInputResolutionOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QUrl::UserInputResolutionOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QUrl_UserInputResolutionOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUrl::AceProcessingOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUrl_AceProcessingOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QUrl::AceProcessingOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_QUrl_AceProcessingOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUrl >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUrl_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUrlQuery >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUrlQuery_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUuid::Variant >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUuid_Variant_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUuid::Version >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUuid_Version_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUuid::StringFormat >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUuid_StringFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUuid >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QUuid_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVariantAnimation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QVariantAnimation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVersionNumber >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QVersionNumber_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QWaitCondition >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QWaitCondition_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QWinEventNotifier >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QWinEventNotifier_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QWriteLocker >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QWriteLocker_IDX]); }
#endif
template<> inline PyTypeObject *SbkType< ::QXmlStreamAttribute >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamAttribute_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamAttributes >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamAttributes_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamEntityDeclaration >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamEntityDeclaration_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamEntityResolver >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamEntityResolver_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamNamespaceDeclaration >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamNamespaceDeclaration_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamNotationDeclaration >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamNotationDeclaration_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamReader::TokenType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamReader_TokenType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamReader::ReadElementTextBehaviour >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamReader_ReadElementTextBehaviour_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamReader::Error >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamReader_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamReader >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamReader_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamWriter::Error >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamWriter_Error_IDX]); }
template<> inline PyTypeObject *SbkType< ::QXmlStreamWriter >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QXmlStreamWriter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::GlobalColor >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_GlobalColor_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ColorScheme >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ColorScheme_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ContrastPreference >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ContrastPreference_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::MouseButton >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_MouseButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::MouseButton> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_MouseButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::Orientation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_Orientation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::Orientation> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_Orientation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::FocusPolicy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_FocusPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TabFocusBehavior >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TabFocusBehavior_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::SortOrder >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_SortOrder_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::SplitBehaviorFlags >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_SplitBehaviorFlags_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::SplitBehaviorFlags> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_SplitBehaviorFlags_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TileRule >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TileRule_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::AlignmentFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_AlignmentFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::AlignmentFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_AlignmentFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TextFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TextFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TextElideMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TextElideMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::WhiteSpaceMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_WhiteSpaceMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::HitTestAccuracy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_HitTestAccuracy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::WindowType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_WindowType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::WindowType> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_WindowType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::WindowState >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_WindowState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::WindowState> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_WindowState_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ApplicationState >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ApplicationState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::ApplicationState> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_ApplicationState_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ScreenOrientation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ScreenOrientation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::ScreenOrientation> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_ScreenOrientation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::WidgetAttribute >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_WidgetAttribute_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ApplicationAttribute >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ApplicationAttribute_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ImageConversionFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ImageConversionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::ImageConversionFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_ImageConversionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::BGMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_BGMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::Key >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_Key_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::KeyboardModifier >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_KeyboardModifier_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::KeyboardModifier> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_KeyboardModifier_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::Modifier >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_Modifier_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ArrowType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ArrowType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::PenStyle >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_PenStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::PenCapStyle >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_PenCapStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::PenJoinStyle >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_PenJoinStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::BrushStyle >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_BrushStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::SizeMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_SizeMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::UIEffect >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_UIEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::CursorShape >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_CursorShape_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TextFormat >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TextFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::AspectRatioMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_AspectRatioMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::DockWidgetArea >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_DockWidgetArea_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::DockWidgetArea> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_DockWidgetArea_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::DockWidgetAreaSizes >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_DockWidgetAreaSizes_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ToolBarArea >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ToolBarArea_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::ToolBarArea> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_ToolBarArea_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ToolBarAreaSizes >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ToolBarAreaSizes_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::DateFormat >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_DateFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TimeSpec >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TimeSpec_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::DayOfWeek >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_DayOfWeek_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ScrollBarPolicy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ScrollBarPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::CaseSensitivity >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_CaseSensitivity_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::Corner >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_Corner_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::Edge >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_Edge_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::Edge> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_Edge_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ConnectionType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ConnectionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ShortcutContext >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ShortcutContext_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::FillRule >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_FillRule_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::MaskMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_MaskMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ClipOperation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ClipOperation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ItemSelectionMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ItemSelectionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ItemSelectionOperation >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ItemSelectionOperation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TransformationMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TransformationMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::Axis >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_Axis_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::FocusReason >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_FocusReason_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ContextMenuPolicy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ContextMenuPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ContextMenuTrigger >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ContextMenuTrigger_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::InputMethodQuery >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_InputMethodQuery_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::InputMethodQuery> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_InputMethodQuery_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::InputMethodHint >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_InputMethodHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::InputMethodHint> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_InputMethodHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::EnterKeyType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_EnterKeyType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ToolButtonStyle >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ToolButtonStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::LayoutDirection >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_LayoutDirection_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::AnchorPoint >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_AnchorPoint_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::FindChildOption >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_FindChildOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::FindChildOption> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_FindChildOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::DropAction >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_DropAction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::DropAction> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_DropAction_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::CheckState >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_CheckState_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ItemDataRole >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ItemDataRole_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ItemFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ItemFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::ItemFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_ItemFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::MatchFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_MatchFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::MatchFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_MatchFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::WindowModality >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_WindowModality_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TextInteractionFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TextInteractionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::TextInteractionFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_TextInteractionFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::EventPriority >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_EventPriority_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::SizeHint >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_SizeHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::WindowFrameSection >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_WindowFrameSection_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::CoordinateSystem >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_CoordinateSystem_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TouchPointState >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TouchPointState_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::TouchPointState> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_TouchPointState_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::GestureState >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_GestureState_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::GestureType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_GestureType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::GestureFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_GestureFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::GestureFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_GestureFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::NativeGestureType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_NativeGestureType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::NavigationMode >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_NavigationMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::CursorMoveStyle >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_CursorMoveStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TimerType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TimerType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::TimerId >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_TimerId_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ScrollPhase >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ScrollPhase_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::MouseEventSource >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_MouseEventSource_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::MouseEventFlag >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_MouseEventFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt::MouseEventFlag> >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QFlags_Qt_MouseEventFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ChecksumType >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ChecksumType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::HighDpiScaleFactorRoundingPolicy >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_HighDpiScaleFactorRoundingPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::PermissionStatus >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_PermissionStatus_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt::ReturnByValueConstant >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_Qt_ReturnByValueConstant_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCoreHelper::QDirListingIterator >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QtCoreHelper_QDirListingIterator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCoreHelper::QGenericArgumentHolder >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QtCoreHelper_QGenericArgumentHolder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCoreHelper::QGenericReturnArgumentHolder >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QtCoreHelper_QGenericReturnArgumentHolder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QtCoreHelper::QIOPipe >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QtCoreHelper_QIOPipe_IDX]); }
#if QT_CONFIG(thread)
template<> inline PyTypeObject *SbkType< ::QtCoreHelper::QMutexLocker >() { return Shiboken::Module::get(SbkPySide6_QtCoreTypeStructs[SBK_QtCoreHelper_QMutexLocker_IDX]); }
#endif

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTCORE_PYTHON_H

