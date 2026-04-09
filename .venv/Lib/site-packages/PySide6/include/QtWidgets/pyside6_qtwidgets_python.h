// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QTWIDGETS_PYTHON_H
#define SBK_QTWIDGETS_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>

// Bound library includes
#include <QFormLayout>
#include <QTextEdit>
#include <QtGui/qfilesystemmodel.h>
#include <QtWidgets/qabstractitemdelegate.h>
#include <QtWidgets/qabstractitemview.h>
#include <QtWidgets/qabstractscrollarea.h>
#include <QtWidgets/qabstractslider.h>
#include <QtWidgets/qabstractspinbox.h>
#include <QtWidgets/qboxlayout.h>
#include <QtWidgets/qcalendarwidget.h>
#include <QtWidgets/qcolordialog.h>
#include <QtWidgets/qcolormap.h>
#include <QtWidgets/qcombobox.h>
#include <QtWidgets/qcompleter.h>
#include <QtWidgets/qdatawidgetmapper.h>
#include <QtWidgets/qdatetimeedit.h>
#include <QtWidgets/qdialog.h>
#include <QtWidgets/qdialogbuttonbox.h>
#include <QtWidgets/qdockwidget.h>
#include <QtWidgets/qfiledialog.h>
#include <QtWidgets/qfontcombobox.h>
#include <QtWidgets/qfontdialog.h>
#include <QtWidgets/qformlayout.h>
#include <QtWidgets/qframe.h>
#include <QtWidgets/qgesture.h>
#include <QtWidgets/qgesturerecognizer.h>
#include <QtWidgets/qgraphicseffect.h>
#include <QtWidgets/qgraphicsitem.h>
#include <QtWidgets/qgraphicsscene.h>
#include <QtWidgets/qgraphicssceneevent.h>
#include <QtWidgets/qgraphicsview.h>
#include <QtWidgets/qheaderview.h>
#include <QtWidgets/qinputdialog.h>
#include <QtWidgets/qlayout.h>
#include <QtWidgets/qlcdnumber.h>
#include <QtWidgets/qlineedit.h>
#include <QtWidgets/qlistview.h>
#include <QtWidgets/qlistwidget.h>
#include <QtWidgets/qmainwindow.h>
#include <QtWidgets/qmdiarea.h>
#include <QtWidgets/qmdisubwindow.h>
#include <QtWidgets/qmessagebox.h>
#include <QtWidgets/qplaintextedit.h>
#include <QtWidgets/qprogressbar.h>
#include <QtWidgets/qrhiwidget.h>
#include <QtWidgets/qrubberband.h>
#include <QtWidgets/qscroller.h>
#include <QtWidgets/qscrollerproperties.h>
#include <QtWidgets/qsizepolicy.h>
#include <QtWidgets/qslider.h>
#include <QtWidgets/qstackedlayout.h>
#include <QtWidgets/qstyle.h>
#include <QtWidgets/qstyleoption.h>
#include <QtWidgets/qsystemtrayicon.h>
#include <QtWidgets/qtabbar.h>
#include <QtWidgets/qtablewidget.h>
#include <QtWidgets/qtabwidget.h>
#include <QtWidgets/qtextedit.h>
#include <QtWidgets/qtoolbutton.h>
#include <QtWidgets/qtreewidget.h>
#include <QtWidgets/qtreewidgetitemiterator.h>
#include <QtWidgets/qwidget.h>
#include <QtWidgets/qwizard.h>

QT_BEGIN_NAMESPACE
class QAbstractButton;
class QAbstractGraphicsShapeItem;
class QAccessibleWidget;
class QApplication;
class QButtonGroup;
class QCheckBox;
class QColumnView;
class QCommandLinkButton;
class QCommonStyle;
class QDateEdit;
class QDial;
class QDoubleSpinBox;
class QErrorMessage;
class QFileIconProvider;
class QFocusFrame;
class QGestureEvent;
class QGraphicsAnchor;
class QGraphicsAnchorLayout;
class QGraphicsColorizeEffect;
class QGraphicsDropShadowEffect;
class QGraphicsEllipseItem;
class QGraphicsGridLayout;
class QGraphicsItemAnimation;
class QGraphicsItemGroup;
class QGraphicsLayout;
class QGraphicsLayoutItem;
class QGraphicsLineItem;
class QGraphicsLinearLayout;
class QGraphicsObject;
class QGraphicsOpacityEffect;
class QGraphicsPathItem;
class QGraphicsPolygonItem;
class QGraphicsProxyWidget;
class QGraphicsRectItem;
class QGraphicsRotation;
class QGraphicsScale;
class QGraphicsSceneDragDropEvent;
class QGraphicsSceneEvent;
class QGraphicsSceneHelpEvent;
class QGraphicsSceneHoverEvent;
class QGraphicsSceneMouseEvent;
class QGraphicsSceneMoveEvent;
class QGraphicsSceneResizeEvent;
class QGraphicsSceneWheelEvent;
class QGraphicsSimpleTextItem;
class QGraphicsTextItem;
class QGraphicsTransform;
class QGraphicsWidget;
class QGridLayout;
class QGroupBox;
class QHBoxLayout;
class QItemDelegate;
class QItemEditorCreatorBase;
class QItemEditorFactory;
class QKeySequenceEdit;
class QLabel;
class QLayoutItem;
class QListWidget;
class QMenu;
class QMenuBar;
class QPanGesture;
class QPlainTextDocumentLayout;
class QProgressDialog;
class QProxyStyle;
class QPushButton;
class QRadioButton;
class QScrollArea;
class QScrollBar;
class QSizeGrip;
class QSpacerItem;
class QSpinBox;
class QSplashScreen;
class QSplitter;
class QSplitterHandle;
class QStackedWidget;
class QStatusBar;
class QStyleFactory;
class QStylePainter;
class QStyledItemDelegate;
class QTableView;
class QTableWidget;
class QTableWidgetSelectionRange;
class QTapAndHoldGesture;
class QTapGesture;
class QTextBrowser;
struct QTileRules;
class QTimeEdit;
class QToolBar;
class QToolBox;
class QToolTip;
class QTreeView;
class QTreeWidget;
class QUndoView;
class QVBoxLayout;
class QWhatsThis;
class QWidgetAction;
class QWidgetItem;
class QWizardPage;
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_QAbstractButton_IDX                                  = 0,
    SBK_QAbstractGraphicsShapeItem_IDX                       = 1,
    SBK_QAbstractItemDelegate_EndEditHint_IDX                = 3,
    SBK_QAbstractItemDelegate_IDX                            = 2,
    SBK_QAbstractItemView_SelectionMode_IDX                  = 12,
    SBK_QAbstractItemView_SelectionBehavior_IDX              = 11,
    SBK_QAbstractItemView_ScrollHint_IDX                     = 9,
    SBK_QAbstractItemView_EditTrigger_IDX                    = 8,
    SBK_QFlags_QAbstractItemView_EditTrigger_IDX             = 74,
    SBK_QAbstractItemView_ScrollMode_IDX                     = 10,
    SBK_QAbstractItemView_DragDropMode_IDX                   = 6,
    SBK_QAbstractItemView_CursorAction_IDX                   = 5,
    SBK_QAbstractItemView_State_IDX                          = 13,
    SBK_QAbstractItemView_DropIndicatorPosition_IDX          = 7,
    SBK_QAbstractItemView_IDX                                = 4,
    SBK_QAbstractScrollArea_SizeAdjustPolicy_IDX             = 15,
    SBK_QAbstractScrollArea_IDX                              = 14,
    SBK_QAbstractSlider_SliderAction_IDX                     = 17,
    SBK_QAbstractSlider_SliderChange_IDX                     = 18,
    SBK_QAbstractSlider_IDX                                  = 16,
    SBK_QAbstractSpinBox_StepEnabledFlag_IDX                 = 22,
    SBK_QFlags_QAbstractSpinBox_StepEnabledFlag_IDX          = 75,
    SBK_QAbstractSpinBox_ButtonSymbols_IDX                   = 20,
    SBK_QAbstractSpinBox_CorrectionMode_IDX                  = 21,
    SBK_QAbstractSpinBox_StepType_IDX                        = 23,
    SBK_QAbstractSpinBox_IDX                                 = 19,
    SBK_QAccessibleWidget_IDX                                = 24,
    SBK_QApplication_IDX                                     = 25,
    SBK_QBoxLayout_Direction_IDX                             = 27,
    SBK_QBoxLayout_IDX                                       = 26,
    SBK_QButtonGroup_IDX                                     = 28,
    SBK_QCalendarWidget_HorizontalHeaderFormat_IDX           = 30,
    SBK_QCalendarWidget_VerticalHeaderFormat_IDX             = 32,
    SBK_QCalendarWidget_SelectionMode_IDX                    = 31,
    SBK_QCalendarWidget_IDX                                  = 29,
    SBK_QCheckBox_IDX                                        = 33,
    SBK_QColorDialog_ColorDialogOption_IDX                   = 35,
    SBK_QFlags_QColorDialog_ColorDialogOption_IDX            = 76,
    SBK_QColorDialog_IDX                                     = 34,
    SBK_QColormap_Mode_IDX                                   = 37,
    SBK_QColormap_IDX                                        = 36,
    SBK_QColumnView_IDX                                      = 38,
    SBK_QComboBox_InsertPolicy_IDX                           = 40,
    SBK_QComboBox_SizeAdjustPolicy_IDX                       = 42,
    SBK_QComboBox_LabelDrawingMode_IDX                       = 41,
    SBK_QComboBox_IDX                                        = 39,
    SBK_QCommandLinkButton_IDX                               = 43,
    SBK_QCommonStyle_IDX                                     = 44,
    SBK_QCompleter_CompletionMode_IDX                        = 46,
    SBK_QCompleter_ModelSorting_IDX                          = 47,
    SBK_QCompleter_IDX                                       = 45,
    SBK_QDataWidgetMapper_SubmitPolicy_IDX                   = 49,
    SBK_QDataWidgetMapper_IDX                                = 48,
    SBK_QDateEdit_IDX                                        = 50,
    SBK_QDateTimeEdit_Section_IDX                            = 52,
    SBK_QFlags_QDateTimeEdit_Section_IDX                     = 77,
    SBK_QDateTimeEdit_IDX                                    = 51,
    SBK_QDial_IDX                                            = 53,
    SBK_QDialog_DialogCode_IDX                               = 55,
    SBK_QDialog_IDX                                          = 54,
    SBK_QDialogButtonBox_ButtonRole_IDX                      = 58,
    SBK_QDialogButtonBox_StandardButton_IDX                  = 59,
    SBK_QFlags_QDialogButtonBox_StandardButton_IDX           = 78,
    SBK_QDialogButtonBox_ButtonLayout_IDX                    = 57,
    SBK_QDialogButtonBox_IDX                                 = 56,
    SBK_QDockWidget_DockWidgetFeature_IDX                    = 61,
    SBK_QFlags_QDockWidget_DockWidgetFeature_IDX             = 79,
    SBK_QDockWidget_IDX                                      = 60,
    SBK_QDoubleSpinBox_IDX                                   = 62,
    SBK_QErrorMessage_IDX                                    = 63,
    SBK_QFileDialog_ViewMode_IDX                             = 69,
    SBK_QFileDialog_FileMode_IDX                             = 67,
    SBK_QFileDialog_AcceptMode_IDX                           = 65,
    SBK_QFileDialog_DialogLabel_IDX                          = 66,
    SBK_QFileDialog_Option_IDX                               = 68,
    SBK_QFlags_QFileDialog_Option_IDX                        = 80,
    SBK_QFileDialog_IDX                                      = 64,
    SBK_QFileIconProvider_IDX                                = 70,
    SBK_QFileSystemModel_Roles_IDX                           = 73,
    SBK_QFileSystemModel_Option_IDX                          = 72,
    SBK_QFlags_QFileSystemModel_Option_IDX                   = 81,
    SBK_QFileSystemModel_IDX                                 = 71,
    SBK_QFocusFrame_IDX                                      = 111,
    SBK_QFontComboBox_FontFilter_IDX                         = 113,
    SBK_QFlags_QFontComboBox_FontFilter_IDX                  = 82,
    SBK_QFontComboBox_IDX                                    = 112,
    SBK_QFontDialog_FontDialogOption_IDX                     = 115,
    SBK_QFlags_QFontDialog_FontDialogOption_IDX              = 83,
    SBK_QFontDialog_IDX                                      = 114,
    SBK_QFormLayout_FieldGrowthPolicy_IDX                    = 117,
    SBK_QFormLayout_RowWrapPolicy_IDX                        = 119,
    SBK_QFormLayout_ItemRole_IDX                             = 118,
    SBK_QFormLayout_IDX                                      = 116,
    SBK_QFormLayout_TakeRowResult_IDX                        = 120,
    SBK_QFrame_Shape_IDX                                     = 123,
    SBK_QFrame_Shadow_IDX                                    = 122,
    SBK_QFrame_StyleMask_IDX                                 = 124,
    SBK_QFrame_IDX                                           = 121,
    SBK_QGesture_GestureCancelPolicy_IDX                     = 126,
    SBK_QGesture_IDX                                         = 125,
    SBK_QGestureEvent_IDX                                    = 127,
    SBK_QGestureRecognizer_ResultFlag_IDX                    = 129,
    SBK_QFlags_QGestureRecognizer_ResultFlag_IDX             = 84,
    SBK_QGestureRecognizer_IDX                               = 128,
    SBK_QGraphicsAnchor_IDX                                  = 130,
    SBK_QGraphicsAnchorLayout_IDX                            = 131,
    SBK_QGraphicsBlurEffect_BlurHint_IDX                     = 133,
    SBK_QFlags_QGraphicsBlurEffect_BlurHint_IDX              = 85,
    SBK_QGraphicsBlurEffect_IDX                              = 132,
    SBK_QGraphicsColorizeEffect_IDX                          = 134,
    SBK_QGraphicsDropShadowEffect_IDX                        = 135,
    SBK_QGraphicsEffect_ChangeFlag_IDX                       = 137,
    SBK_QFlags_QGraphicsEffect_ChangeFlag_IDX                = 86,
    SBK_QGraphicsEffect_PixmapPadMode_IDX                    = 138,
    SBK_QGraphicsEffect_IDX                                  = 136,
    SBK_QGraphicsEllipseItem_IDX                             = 139,
    SBK_QGraphicsGridLayout_IDX                              = 140,
    SBK_QGraphicsItem_GraphicsItemFlag_IDX                   = 145,
    SBK_QFlags_QGraphicsItem_GraphicsItemFlag_IDX            = 87,
    SBK_QGraphicsItem_GraphicsItemChange_IDX                 = 144,
    SBK_QGraphicsItem_CacheMode_IDX                          = 142,
    SBK_QGraphicsItem_PanelModality_IDX                      = 146,
    SBK_QGraphicsItem_Extension_IDX                          = 143,
    SBK_QGraphicsItem_IDX                                    = 141,
    SBK_QGraphicsItemAnimation_IDX                           = 147,
    SBK_QGraphicsItemGroup_IDX                               = 148,
    SBK_QGraphicsLayout_IDX                                  = 149,
    SBK_QGraphicsLayoutItem_IDX                              = 150,
    SBK_QGraphicsLineItem_IDX                                = 151,
    SBK_QGraphicsLinearLayout_IDX                            = 152,
    SBK_QGraphicsObject_IDX                                  = 153,
    SBK_QGraphicsOpacityEffect_IDX                           = 154,
    SBK_QGraphicsPathItem_IDX                                = 155,
    SBK_QGraphicsPixmapItem_ShapeMode_IDX                    = 157,
    SBK_QGraphicsPixmapItem_IDX                              = 156,
    SBK_QGraphicsPolygonItem_IDX                             = 158,
    SBK_QGraphicsProxyWidget_IDX                             = 159,
    SBK_QGraphicsRectItem_IDX                                = 160,
    SBK_QGraphicsRotation_IDX                                = 161,
    SBK_QGraphicsScale_IDX                                   = 162,
    SBK_QGraphicsScene_ItemIndexMethod_IDX                   = 164,
    SBK_QGraphicsScene_SceneLayer_IDX                        = 165,
    SBK_QFlags_QGraphicsScene_SceneLayer_IDX                 = 88,
    SBK_QGraphicsScene_IDX                                   = 163,
    SBK_QGraphicsSceneContextMenuEvent_Reason_IDX            = 167,
    SBK_QGraphicsSceneContextMenuEvent_IDX                   = 166,
    SBK_QGraphicsSceneDragDropEvent_IDX                      = 168,
    SBK_QGraphicsSceneEvent_IDX                              = 169,
    SBK_QGraphicsSceneHelpEvent_IDX                          = 170,
    SBK_QGraphicsSceneHoverEvent_IDX                         = 171,
    SBK_QGraphicsSceneMouseEvent_IDX                         = 172,
    SBK_QGraphicsSceneMoveEvent_IDX                          = 173,
    SBK_QGraphicsSceneResizeEvent_IDX                        = 174,
    SBK_QGraphicsSceneWheelEvent_IDX                         = 175,
    SBK_QGraphicsSimpleTextItem_IDX                          = 176,
    SBK_QGraphicsTextItem_IDX                                = 177,
    SBK_QGraphicsTransform_IDX                               = 178,
    SBK_QGraphicsView_ViewportAnchor_IDX                     = 183,
    SBK_QGraphicsView_CacheModeFlag_IDX                      = 180,
    SBK_QFlags_QGraphicsView_CacheModeFlag_IDX               = 89,
    SBK_QGraphicsView_DragMode_IDX                           = 181,
    SBK_QGraphicsView_ViewportUpdateMode_IDX                 = 184,
    SBK_QGraphicsView_OptimizationFlag_IDX                   = 182,
    SBK_QFlags_QGraphicsView_OptimizationFlag_IDX            = 90,
    SBK_QGraphicsView_IDX                                    = 179,
    SBK_QGraphicsWidget_IDX                                  = 185,
    SBK_QGridLayout_IDX                                      = 186,
    SBK_QGroupBox_IDX                                        = 187,
    SBK_QHBoxLayout_IDX                                      = 188,
    SBK_QHeaderView_ResizeMode_IDX                           = 190,
    SBK_QHeaderView_IDX                                      = 189,
    SBK_QInputDialog_InputDialogOption_IDX                   = 192,
    SBK_QInputDialog_InputMode_IDX                           = 193,
    SBK_QInputDialog_IDX                                     = 191,
    SBK_QItemDelegate_IDX                                    = 194,
    SBK_QItemEditorCreatorBase_IDX                           = 195,
    SBK_QItemEditorFactory_IDX                               = 196,
    SBK_QKeySequenceEdit_IDX                                 = 197,
    SBK_QLCDNumber_Mode_IDX                                  = 199,
    SBK_QLCDNumber_SegmentStyle_IDX                          = 200,
    SBK_QLCDNumber_IDX                                       = 198,
    SBK_QLabel_IDX                                           = 201,
    SBK_QLayout_SizeConstraint_IDX                           = 203,
    SBK_QLayout_IDX                                          = 202,
    SBK_QLayoutItem_IDX                                      = 204,
    SBK_QLineEdit_ActionPosition_IDX                         = 206,
    SBK_QLineEdit_EchoMode_IDX                               = 207,
    SBK_QLineEdit_IDX                                        = 205,
    SBK_QListView_Movement_IDX                               = 211,
    SBK_QListView_Flow_IDX                                   = 209,
    SBK_QListView_ResizeMode_IDX                             = 212,
    SBK_QListView_LayoutMode_IDX                             = 210,
    SBK_QListView_ViewMode_IDX                               = 213,
    SBK_QListView_IDX                                        = 208,
    SBK_QListWidget_IDX                                      = 214,
    SBK_QListWidgetItem_ItemType_IDX                         = 216,
    SBK_QListWidgetItem_IDX                                  = 215,
    SBK_QMainWindow_DockOption_IDX                           = 218,
    SBK_QFlags_QMainWindow_DockOption_IDX                    = 91,
    SBK_QMainWindow_IDX                                      = 217,
    SBK_QMdiArea_AreaOption_IDX                              = 220,
    SBK_QFlags_QMdiArea_AreaOption_IDX                       = 92,
    SBK_QMdiArea_WindowOrder_IDX                             = 222,
    SBK_QMdiArea_ViewMode_IDX                                = 221,
    SBK_QMdiArea_IDX                                         = 219,
    SBK_QMdiSubWindow_SubWindowOption_IDX                    = 224,
    SBK_QFlags_QMdiSubWindow_SubWindowOption_IDX             = 93,
    SBK_QMdiSubWindow_IDX                                    = 223,
    SBK_QMenu_IDX                                            = 225,
    SBK_QMenuBar_IDX                                         = 226,
    SBK_QMessageBox_Option_IDX                               = 230,
    SBK_QFlags_QMessageBox_Option_IDX                        = 94,
    SBK_QMessageBox_Icon_IDX                                 = 229,
    SBK_QMessageBox_ButtonRole_IDX                           = 228,
    SBK_QMessageBox_StandardButton_IDX                       = 231,
    SBK_QFlags_QMessageBox_StandardButton_IDX                = 95,
    SBK_QMessageBox_IDX                                      = 227,
    SBK_QPanGesture_IDX                                      = 232,
    SBK_QPinchGesture_ChangeFlag_IDX                         = 234,
    SBK_QFlags_QPinchGesture_ChangeFlag_IDX                  = 96,
    SBK_QPinchGesture_IDX                                    = 233,
    SBK_QPlainTextDocumentLayout_IDX                         = 235,
    SBK_QPlainTextEdit_LineWrapMode_IDX                      = 237,
    SBK_QPlainTextEdit_IDX                                   = 236,
    SBK_QProgressBar_Direction_IDX                           = 239,
    SBK_QProgressBar_IDX                                     = 238,
    SBK_QProgressDialog_IDX                                  = 240,
    SBK_QProxyStyle_IDX                                      = 241,
    SBK_QPushButton_IDX                                      = 242,
    SBK_QRadioButton_IDX                                     = 243,
    SBK_QRhiWidget_Api_IDX                                   = 245,
    SBK_QRhiWidget_TextureFormat_IDX                         = 246,
    SBK_QRhiWidget_IDX                                       = 244,
    SBK_QRubberBand_Shape_IDX                                = 248,
    SBK_QRubberBand_IDX                                      = 247,
    SBK_QScrollArea_IDX                                      = 249,
    SBK_QScrollBar_IDX                                       = 250,
    SBK_QScroller_State_IDX                                  = 254,
    SBK_QScroller_ScrollerGestureType_IDX                    = 253,
    SBK_QScroller_Input_IDX                                  = 252,
    SBK_QScroller_IDX                                        = 251,
    SBK_QScrollerProperties_OvershootPolicy_IDX              = 257,
    SBK_QScrollerProperties_FrameRates_IDX                   = 256,
    SBK_QScrollerProperties_ScrollMetric_IDX                 = 258,
    SBK_QScrollerProperties_IDX                              = 255,
    SBK_QSizeGrip_IDX                                        = 259,
    SBK_QSizePolicy_PolicyFlag_IDX                           = 263,
    SBK_QSizePolicy_Policy_IDX                               = 262,
    SBK_QSizePolicy_ControlType_IDX                          = 261,
    SBK_QFlags_QSizePolicy_ControlType_IDX                   = 97,
    SBK_QSizePolicy_IDX                                      = 260,
    SBK_QSlider_TickPosition_IDX                             = 265,
    SBK_QSlider_IDX                                          = 264,
    SBK_QSpacerItem_IDX                                      = 266,
    SBK_QSpinBox_IDX                                         = 267,
    SBK_QSplashScreen_IDX                                    = 268,
    SBK_QSplitter_IDX                                        = 269,
    SBK_QSplitterHandle_IDX                                  = 270,
    SBK_QStackedLayout_StackingMode_IDX                      = 272,
    SBK_QStackedLayout_IDX                                   = 271,
    SBK_QStackedWidget_IDX                                   = 273,
    SBK_QStatusBar_IDX                                       = 274,
    SBK_QStyle_StateFlag_IDX                                 = 283,
    SBK_QFlags_QStyle_StateFlag_IDX                          = 98,
    SBK_QStyle_PrimitiveElement_IDX                          = 280,
    SBK_QStyle_ControlElement_IDX                            = 278,
    SBK_QStyle_SubElement_IDX                                = 286,
    SBK_QStyle_ComplexControl_IDX                            = 276,
    SBK_QStyle_SubControl_IDX                                = 285,
    SBK_QFlags_QStyle_SubControl_IDX                         = 99,
    SBK_QStyle_PixelMetric_IDX                               = 279,
    SBK_QStyle_ContentsType_IDX                              = 277,
    SBK_QStyle_RequestSoftwareInputPanel_IDX                 = 281,
    SBK_QStyle_StyleHint_IDX                                 = 284,
    SBK_QStyle_StandardPixmap_IDX                            = 282,
    SBK_QStyle_IDX                                           = 275,
    SBK_QStyleFactory_IDX                                    = 287,
    SBK_QStyleHintReturn_HintReturnType_IDX                  = 289,
    SBK_QStyleHintReturn_StyleOptionType_IDX                 = 290,
    SBK_QStyleHintReturn_StyleOptionVersion_IDX              = 291,
    SBK_QStyleHintReturn_IDX                                 = 288,
    SBK_QStyleHintReturnMask_StyleOptionType_IDX             = 293,
    SBK_QStyleHintReturnMask_StyleOptionVersion_IDX          = 294,
    SBK_QStyleHintReturnMask_IDX                             = 292,
    SBK_QStyleHintReturnVariant_StyleOptionType_IDX          = 296,
    SBK_QStyleHintReturnVariant_StyleOptionVersion_IDX       = 297,
    SBK_QStyleHintReturnVariant_IDX                          = 295,
    SBK_QStyleOption_OptionType_IDX                          = 299,
    SBK_QStyleOption_StyleOptionType_IDX                     = 300,
    SBK_QStyleOption_StyleOptionVersion_IDX                  = 301,
    SBK_QStyleOption_IDX                                     = 298,
    SBK_QStyleOptionButton_StyleOptionType_IDX               = 304,
    SBK_QStyleOptionButton_StyleOptionVersion_IDX            = 305,
    SBK_QStyleOptionButton_ButtonFeature_IDX                 = 303,
    SBK_QFlags_QStyleOptionButton_ButtonFeature_IDX          = 100,
    SBK_QStyleOptionButton_IDX                               = 302,
    SBK_QStyleOptionComboBox_StyleOptionType_IDX             = 307,
    SBK_QStyleOptionComboBox_StyleOptionVersion_IDX          = 308,
    SBK_QStyleOptionComboBox_IDX                             = 306,
    SBK_QStyleOptionComplex_StyleOptionType_IDX              = 310,
    SBK_QStyleOptionComplex_StyleOptionVersion_IDX           = 311,
    SBK_QStyleOptionComplex_IDX                              = 309,
    SBK_QStyleOptionDockWidget_StyleOptionType_IDX           = 313,
    SBK_QStyleOptionDockWidget_StyleOptionVersion_IDX        = 314,
    SBK_QStyleOptionDockWidget_IDX                           = 312,
    SBK_QStyleOptionFocusRect_StyleOptionType_IDX            = 316,
    SBK_QStyleOptionFocusRect_StyleOptionVersion_IDX         = 317,
    SBK_QStyleOptionFocusRect_IDX                            = 315,
    SBK_QStyleOptionFrame_StyleOptionType_IDX                = 320,
    SBK_QStyleOptionFrame_StyleOptionVersion_IDX             = 321,
    SBK_QStyleOptionFrame_FrameFeature_IDX                   = 319,
    SBK_QFlags_QStyleOptionFrame_FrameFeature_IDX            = 101,
    SBK_QStyleOptionFrame_IDX                                = 318,
    SBK_QStyleOptionGraphicsItem_StyleOptionType_IDX         = 323,
    SBK_QStyleOptionGraphicsItem_StyleOptionVersion_IDX      = 324,
    SBK_QStyleOptionGraphicsItem_IDX                         = 322,
    SBK_QStyleOptionGroupBox_StyleOptionType_IDX             = 326,
    SBK_QStyleOptionGroupBox_StyleOptionVersion_IDX          = 327,
    SBK_QStyleOptionGroupBox_IDX                             = 325,
    SBK_QStyleOptionHeader_StyleOptionType_IDX               = 332,
    SBK_QStyleOptionHeader_StyleOptionVersion_IDX            = 333,
    SBK_QStyleOptionHeader_SectionPosition_IDX               = 329,
    SBK_QStyleOptionHeader_SelectedPosition_IDX              = 330,
    SBK_QStyleOptionHeader_SortIndicator_IDX                 = 331,
    SBK_QStyleOptionHeader_IDX                               = 328,
    SBK_QStyleOptionHeaderV2_StyleOptionType_IDX             = 335,
    SBK_QStyleOptionHeaderV2_StyleOptionVersion_IDX          = 336,
    SBK_QStyleOptionHeaderV2_IDX                             = 334,
    SBK_QStyleOptionMenuItem_StyleOptionType_IDX             = 340,
    SBK_QStyleOptionMenuItem_StyleOptionVersion_IDX          = 341,
    SBK_QStyleOptionMenuItem_MenuItemType_IDX                = 339,
    SBK_QStyleOptionMenuItem_CheckType_IDX                   = 338,
    SBK_QStyleOptionMenuItem_IDX                             = 337,
    SBK_QStyleOptionMenuItemV2_StyleOptionVersion_IDX        = 343,
    SBK_QStyleOptionMenuItemV2_IDX                           = 342,
    SBK_QStyleOptionProgressBar_StyleOptionType_IDX          = 345,
    SBK_QStyleOptionProgressBar_StyleOptionVersion_IDX       = 346,
    SBK_QStyleOptionProgressBar_IDX                          = 344,
    SBK_QStyleOptionRubberBand_StyleOptionType_IDX           = 348,
    SBK_QStyleOptionRubberBand_StyleOptionVersion_IDX        = 349,
    SBK_QStyleOptionRubberBand_IDX                           = 347,
    SBK_QStyleOptionSizeGrip_StyleOptionType_IDX             = 351,
    SBK_QStyleOptionSizeGrip_StyleOptionVersion_IDX          = 352,
    SBK_QStyleOptionSizeGrip_IDX                             = 350,
    SBK_QStyleOptionSlider_StyleOptionType_IDX               = 354,
    SBK_QStyleOptionSlider_StyleOptionVersion_IDX            = 355,
    SBK_QStyleOptionSlider_IDX                               = 353,
    SBK_QStyleOptionSpinBox_StyleOptionType_IDX              = 357,
    SBK_QStyleOptionSpinBox_StyleOptionVersion_IDX           = 358,
    SBK_QStyleOptionSpinBox_IDX                              = 356,
    SBK_QStyleOptionTab_StyleOptionType_IDX                  = 362,
    SBK_QStyleOptionTab_StyleOptionVersion_IDX               = 363,
    SBK_QStyleOptionTab_TabPosition_IDX                      = 365,
    SBK_QStyleOptionTab_SelectedPosition_IDX                 = 361,
    SBK_QStyleOptionTab_CornerWidget_IDX                     = 360,
    SBK_QFlags_QStyleOptionTab_CornerWidget_IDX              = 102,
    SBK_QStyleOptionTab_TabFeature_IDX                       = 364,
    SBK_QFlags_QStyleOptionTab_TabFeature_IDX                = 103,
    SBK_QStyleOptionTab_IDX                                  = 359,
    SBK_QStyleOptionTabBarBase_StyleOptionType_IDX           = 367,
    SBK_QStyleOptionTabBarBase_StyleOptionVersion_IDX        = 368,
    SBK_QStyleOptionTabBarBase_IDX                           = 366,
    SBK_QStyleOptionTabWidgetFrame_StyleOptionType_IDX       = 370,
    SBK_QStyleOptionTabWidgetFrame_StyleOptionVersion_IDX    = 371,
    SBK_QStyleOptionTabWidgetFrame_IDX                       = 369,
    SBK_QStyleOptionTitleBar_StyleOptionType_IDX             = 373,
    SBK_QStyleOptionTitleBar_StyleOptionVersion_IDX          = 374,
    SBK_QStyleOptionTitleBar_IDX                             = 372,
    SBK_QStyleOptionToolBar_StyleOptionType_IDX              = 376,
    SBK_QStyleOptionToolBar_StyleOptionVersion_IDX           = 377,
    SBK_QStyleOptionToolBar_ToolBarPosition_IDX              = 379,
    SBK_QStyleOptionToolBar_ToolBarFeature_IDX               = 378,
    SBK_QFlags_QStyleOptionToolBar_ToolBarFeature_IDX        = 104,
    SBK_QStyleOptionToolBar_IDX                              = 375,
    SBK_QStyleOptionToolBox_StyleOptionType_IDX              = 382,
    SBK_QStyleOptionToolBox_StyleOptionVersion_IDX           = 383,
    SBK_QStyleOptionToolBox_TabPosition_IDX                  = 384,
    SBK_QStyleOptionToolBox_SelectedPosition_IDX             = 381,
    SBK_QStyleOptionToolBox_IDX                              = 380,
    SBK_QStyleOptionToolButton_StyleOptionType_IDX           = 386,
    SBK_QStyleOptionToolButton_StyleOptionVersion_IDX        = 387,
    SBK_QStyleOptionToolButton_ToolButtonFeature_IDX         = 388,
    SBK_QFlags_QStyleOptionToolButton_ToolButtonFeature_IDX  = 105,
    SBK_QStyleOptionToolButton_IDX                           = 385,
    SBK_QStyleOptionViewItem_StyleOptionType_IDX             = 391,
    SBK_QStyleOptionViewItem_StyleOptionVersion_IDX          = 392,
    SBK_QStyleOptionViewItem_Position_IDX                    = 390,
    SBK_QStyleOptionViewItem_ViewItemFeature_IDX             = 393,
    SBK_QFlags_QStyleOptionViewItem_ViewItemFeature_IDX      = 106,
    SBK_QStyleOptionViewItem_ViewItemPosition_IDX            = 394,
    SBK_QStyleOptionViewItem_IDX                             = 389,
    SBK_QStylePainter_IDX                                    = 395,
    SBK_QStyledItemDelegate_IDX                              = 396,
    SBK_QSwipeGesture_SwipeDirection_IDX                     = 398,
    SBK_QSwipeGesture_IDX                                    = 397,
    SBK_QSystemTrayIcon_ActivationReason_IDX                 = 400,
    SBK_QSystemTrayIcon_MessageIcon_IDX                      = 401,
    SBK_QSystemTrayIcon_IDX                                  = 399,
    SBK_QTabBar_Shape_IDX                                    = 405,
    SBK_QTabBar_ButtonPosition_IDX                           = 403,
    SBK_QTabBar_SelectionBehavior_IDX                        = 404,
    SBK_QTabBar_IDX                                          = 402,
    SBK_QTabWidget_TabPosition_IDX                           = 407,
    SBK_QTabWidget_TabShape_IDX                              = 408,
    SBK_QTabWidget_IDX                                       = 406,
    SBK_QTableView_IDX                                       = 409,
    SBK_QTableWidget_IDX                                     = 410,
    SBK_QTableWidgetItem_ItemType_IDX                        = 412,
    SBK_QTableWidgetItem_IDX                                 = 411,
    SBK_QTableWidgetSelectionRange_IDX                       = 413,
    SBK_QTapAndHoldGesture_IDX                               = 414,
    SBK_QTapGesture_IDX                                      = 415,
    SBK_QTextBrowser_IDX                                     = 416,
    SBK_QTextEdit_LineWrapMode_IDX                           = 420,
    SBK_QTextEdit_AutoFormattingFlag_IDX                     = 418,
    SBK_QFlags_QTextEdit_AutoFormattingFlag_IDX              = 107,
    SBK_QTextEdit_IDX                                        = 417,
    SBK_QTextEdit_ExtraSelection_IDX                         = 419,
    SBK_QTileRules_IDX                                       = 421,
    SBK_QTimeEdit_IDX                                        = 422,
    SBK_QToolBar_IDX                                         = 423,
    SBK_QToolBox_IDX                                         = 424,
    SBK_QToolButton_ToolButtonPopupMode_IDX                  = 426,
    SBK_QToolButton_IDX                                      = 425,
    SBK_QToolTip_IDX                                         = 427,
    SBK_QTreeView_IDX                                        = 428,
    SBK_QTreeWidget_IDX                                      = 429,
    SBK_QTreeWidgetItem_ItemType_IDX                         = 432,
    SBK_QTreeWidgetItem_ChildIndicatorPolicy_IDX             = 431,
    SBK_QTreeWidgetItem_IDX                                  = 430,
    SBK_QTreeWidgetItemIterator_IteratorFlag_IDX             = 434,
    SBK_QFlags_QTreeWidgetItemIterator_IteratorFlag_IDX      = 108,
    SBK_QTreeWidgetItemIterator_IDX                          = 433,
    SBK_QUndoView_IDX                                        = 435,
    SBK_QVBoxLayout_IDX                                      = 436,
    SBK_QWhatsThis_IDX                                       = 437,
    SBK_QWidget_RenderFlag_IDX                               = 439,
    SBK_QFlags_QWidget_RenderFlag_IDX                        = 109,
    SBK_QWidget_IDX                                          = 438,
    SBK_QWidgetAction_IDX                                    = 440,
    SBK_QWidgetItem_IDX                                      = 441,
    SBK_QWizard_WizardButton_IDX                             = 443,
    SBK_QWizard_WizardPixmap_IDX                             = 445,
    SBK_QWizard_WizardStyle_IDX                              = 446,
    SBK_QWizard_WizardOption_IDX                             = 444,
    SBK_QFlags_QWizard_WizardOption_IDX                      = 110,
    SBK_QWizard_IDX                                          = 442,
    SBK_QWizardPage_IDX                                      = 447,
    SBK_QtWidgets_IDX_COUNT                                  = 448,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_QtWidgetsTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_QtWidgetsModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_QtWidgetsTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QTWIDGETS_QLIST_INT_IDX                              = 0, // QList<int>
    SBK_QTWIDGETS_QLIST_QTREEWIDGETITEMPTR_IDX               = 1, // QList<QTreeWidgetItem*>
    SBK_QTWIDGETS_QLIST_QCOLOR_IDX                           = 2, // QList<QColor>
    SBK_QTWIDGETS_STD_PAIR_QACCESSIBLEINTERFACEPTR_QFLAGS_QACCESSIBLE_RELATIONFLAG_IDX = 3, // std::pair<QAccessibleInterface*,QFlags<QAccessible::RelationFlag>>
    SBK_QTWIDGETS_QLIST_STD_PAIR_QACCESSIBLEINTERFACEPTR_QFLAGS_QACCESSIBLE_RELATIONFLAG_IDX = 4, // QList<std::pair<QAccessibleInterface*,QFlags<QAccessible::RelationFlag>>>
    SBK_QTWIDGETS_QLIST_QGRAPHICSITEMPTR_IDX                 = 5, // QList<QGraphicsItem*>
    SBK_QTWIDGETS_QLIST_QGRAPHICSTRANSFORMPTR_IDX            = 6, // QList<QGraphicsTransform*>
    SBK_QTWIDGETS_QLIST_QACTIONPTR_IDX                       = 7, // QList<QAction*>
    SBK_QTWIDGETS_QLIST_QDOCKWIDGETPTR_IDX                   = 8, // QList<QDockWidget*>
    SBK_QTWIDGETS_QLIST_QKEYCOMBINATION_IDX                  = 9, // QList<QKeyCombination>
    SBK_QTWIDGETS_QLIST_QWIDGETPTR_IDX                       = 10, // QList<QWidget*>
    SBK_QTWIDGETS_QLIST_QTEXTEDIT_EXTRASELECTION_IDX         = 11, // QList<QTextEdit::ExtraSelection>
    SBK_QTWIDGETS_QLIST_QMDISUBWINDOWPTR_IDX                 = 12, // QList<QMdiSubWindow*>
    SBK_QTWIDGETS_QLIST_QRECTF_IDX                           = 13, // QList<QRectF>
    SBK_QTWIDGETS_QLIST_QMODELINDEX_IDX                      = 14, // QList<QModelIndex>
    SBK_QTWIDGETS_QLIST_QTABLEWIDGETITEMPTR_IDX              = 15, // QList<QTableWidgetItem*>
    SBK_QTWIDGETS_QLIST_QTABLEWIDGETSELECTIONRANGE_IDX       = 16, // QList<QTableWidgetSelectionRange>
    SBK_QTWIDGETS_QLIST_QLISTWIDGETITEMPTR_IDX               = 17, // QList<QListWidgetItem*>
    SBK_QTWIDGETS_QLIST_QABSTRACTBUTTONPTR_IDX               = 18, // QList<QAbstractButton*>
    SBK_QTWIDGETS_QLIST_QWIZARD_WIZARDBUTTON_IDX             = 19, // QList<QWizard::WizardButton>
    SBK_QTWIDGETS_QMAP_QDATE_QTEXTCHARFORMAT_IDX             = 20, // QMap<QDate,QTextCharFormat>
    SBK_QTWIDGETS_QLIST_QSCROLLERPTR_IDX                     = 21, // QList<QScroller*>
    SBK_QTWIDGETS_QLIST_QREAL_IDX                            = 22, // QList<qreal>
    SBK_QTWIDGETS_QLIST_QGRAPHICSVIEWPTR_IDX                 = 23, // QList<QGraphicsView*>
    SBK_QTWIDGETS_STD_PAIR_QREAL_QPOINTF_IDX                 = 24, // std::pair<qreal,QPointF>
    SBK_QTWIDGETS_QLIST_STD_PAIR_QREAL_QPOINTF_IDX           = 25, // QList<std::pair<qreal,QPointF>>
    SBK_QTWIDGETS_STD_PAIR_QREAL_QREAL_IDX                   = 26, // std::pair<qreal,qreal>
    SBK_QTWIDGETS_QLIST_STD_PAIR_QREAL_QREAL_IDX             = 27, // QList<std::pair<qreal,qreal>>
    SBK_QTWIDGETS_QLIST_QGESTUREPTR_IDX                      = 28, // QList<QGesture*>
    SBK_QTWIDGETS_QLIST_QURL_IDX                             = 29, // QList<QUrl>
    SBK_QTWIDGETS_QMAP_INT_QVARIANT_IDX                      = 30, // QMap<int,QVariant>
    SBK_QTWIDGETS_QHASH_INT_QBYTEARRAY_IDX                   = 31, // QHash<int,QByteArray>
    SBK_QTWIDGETS_QLIST_QVARIANT_IDX                         = 32, // QList<QVariant>
    SBK_QTWIDGETS_QLIST_QSTRING_IDX                          = 33, // QList<QString>
    SBK_QTWIDGETS_QMAP_QSTRING_QVARIANT_IDX                  = 34, // QMap<QString,QVariant>
    SBK_QTWIDGETS_CONVERTERS_IDX_COUNT                       = 35,
};

// Converter indices
enum : int {
    SBK_QtWidgets_QList_int_IDX                              = 0, // QList<int>
    SBK_QtWidgets_QList_QTreeWidgetItemPTR_IDX               = 1, // QList<QTreeWidgetItem*>
    SBK_QtWidgets_QList_QColor_IDX                           = 2, // QList<QColor>
    SBK_QtWidgets_std_pair_QAccessibleInterfacePTR_QFlags_QAccessible_RelationFlag_IDX = 3, // std::pair<QAccessibleInterface*,QFlags<QAccessible::RelationFlag>>
    SBK_QtWidgets_QList_std_pair_QAccessibleInterfacePTR_QFlags_QAccessible_RelationFlag_IDX = 4, // QList<std::pair<QAccessibleInterface*,QFlags<QAccessible::RelationFlag>>>
    SBK_QtWidgets_QList_QGraphicsItemPTR_IDX                 = 5, // QList<QGraphicsItem*>
    SBK_QtWidgets_QList_QGraphicsTransformPTR_IDX            = 6, // QList<QGraphicsTransform*>
    SBK_QtWidgets_QList_QActionPTR_IDX                       = 7, // QList<QAction*>
    SBK_QtWidgets_QList_QDockWidgetPTR_IDX                   = 8, // QList<QDockWidget*>
    SBK_QtWidgets_QList_QKeyCombination_IDX                  = 9, // QList<QKeyCombination>
    SBK_QtWidgets_QList_QWidgetPTR_IDX                       = 10, // QList<QWidget*>
    SBK_QtWidgets_QList_QTextEdit_ExtraSelection_IDX         = 11, // QList<QTextEdit::ExtraSelection>
    SBK_QtWidgets_QList_QMdiSubWindowPTR_IDX                 = 12, // QList<QMdiSubWindow*>
    SBK_QtWidgets_QList_QRectF_IDX                           = 13, // QList<QRectF>
    SBK_QtWidgets_QList_QModelIndex_IDX                      = 14, // QList<QModelIndex>
    SBK_QtWidgets_QList_QTableWidgetItemPTR_IDX              = 15, // QList<QTableWidgetItem*>
    SBK_QtWidgets_QList_QTableWidgetSelectionRange_IDX       = 16, // QList<QTableWidgetSelectionRange>
    SBK_QtWidgets_QList_QListWidgetItemPTR_IDX               = 17, // QList<QListWidgetItem*>
    SBK_QtWidgets_QList_QAbstractButtonPTR_IDX               = 18, // QList<QAbstractButton*>
    SBK_QtWidgets_QList_QWizard_WizardButton_IDX             = 19, // QList<QWizard::WizardButton>
    SBK_QtWidgets_QMap_QDate_QTextCharFormat_IDX             = 20, // QMap<QDate,QTextCharFormat>
    SBK_QtWidgets_QList_QScrollerPTR_IDX                     = 21, // QList<QScroller*>
    SBK_QtWidgets_QList_qreal_IDX                            = 22, // QList<qreal>
    SBK_QtWidgets_QList_QGraphicsViewPTR_IDX                 = 23, // QList<QGraphicsView*>
    SBK_QtWidgets_std_pair_qreal_QPointF_IDX                 = 24, // std::pair<qreal,QPointF>
    SBK_QtWidgets_QList_std_pair_qreal_QPointF_IDX           = 25, // QList<std::pair<qreal,QPointF>>
    SBK_QtWidgets_std_pair_qreal_qreal_IDX                   = 26, // std::pair<qreal,qreal>
    SBK_QtWidgets_QList_std_pair_qreal_qreal_IDX             = 27, // QList<std::pair<qreal,qreal>>
    SBK_QtWidgets_QList_QGesturePTR_IDX                      = 28, // QList<QGesture*>
    SBK_QtWidgets_QList_QUrl_IDX                             = 29, // QList<QUrl>
    SBK_QtWidgets_QMap_int_QVariant_IDX                      = 30, // QMap<int,QVariant>
    SBK_QtWidgets_QHash_int_QByteArray_IDX                   = 31, // QHash<int,QByteArray>
    SBK_QtWidgets_QList_QVariant_IDX                         = 32, // QList<QVariant>
    SBK_QtWidgets_QList_QString_IDX                          = 33, // QList<QString>
    SBK_QtWidgets_QMap_QString_QVariant_IDX                  = 34, // QMap<QString,QVariant>
    SBK_QtWidgets_CONVERTERS_IDX_COUNT                       = 35,
};
// Macros for type check

// Protected enum surrogates
enum PySide6_QtWidgets_QAbstractItemView_CursorAction_Surrogate : int {};
enum PySide6_QtWidgets_QAbstractItemView_State_Surrogate : int {};
enum PySide6_QtWidgets_QAbstractItemView_DropIndicatorPosition_Surrogate : int {};
enum PySide6_QtWidgets_QAbstractSlider_SliderChange_Surrogate : int {};
enum PySide6_QtWidgets_QGraphicsItem_Extension_Surrogate : int {};

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::QAbstractButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractGraphicsShapeItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractGraphicsShapeItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemDelegate::EndEditHint >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemDelegate_EndEditHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemDelegate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemDelegate_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemView::SelectionMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_SelectionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemView::SelectionBehavior >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_SelectionBehavior_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemView::ScrollHint >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_ScrollHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemView::EditTrigger >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_EditTrigger_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QAbstractItemView::EditTrigger> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QAbstractItemView_EditTrigger_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemView::ScrollMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_ScrollMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemView::DragDropMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_DragDropMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtWidgets_QAbstractItemView_CursorAction_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_CursorAction_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtWidgets_QAbstractItemView_State_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtWidgets_QAbstractItemView_DropIndicatorPosition_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_DropIndicatorPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractItemView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractItemView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractScrollArea::SizeAdjustPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractScrollArea_SizeAdjustPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractScrollArea >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractScrollArea_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSlider::SliderAction >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSlider_SliderAction_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtWidgets_QAbstractSlider_SliderChange_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSlider_SliderChange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSlider >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSlider_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSpinBox::StepEnabledFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSpinBox_StepEnabledFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QAbstractSpinBox::StepEnabledFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QAbstractSpinBox_StepEnabledFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSpinBox::ButtonSymbols >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSpinBox_ButtonSymbols_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSpinBox::CorrectionMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSpinBox_CorrectionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSpinBox::StepType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSpinBox_StepType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAbstractSpinBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAbstractSpinBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QAccessibleWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QAccessibleWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QApplication >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QApplication_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBoxLayout::Direction >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QBoxLayout_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QBoxLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QBoxLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QButtonGroup >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QButtonGroup_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendarWidget::HorizontalHeaderFormat >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCalendarWidget_HorizontalHeaderFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendarWidget::VerticalHeaderFormat >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCalendarWidget_VerticalHeaderFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendarWidget::SelectionMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCalendarWidget_SelectionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCalendarWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCalendarWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCheckBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCheckBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QColorDialog::ColorDialogOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QColorDialog_ColorDialogOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QColorDialog::ColorDialogOption> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QColorDialog_ColorDialogOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QColorDialog >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QColorDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QColormap::Mode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QColormap_Mode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QColormap >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QColormap_IDX]); }
template<> inline PyTypeObject *SbkType< ::QColumnView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QColumnView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QComboBox::InsertPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QComboBox_InsertPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QComboBox::SizeAdjustPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QComboBox_SizeAdjustPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QComboBox::LabelDrawingMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QComboBox_LabelDrawingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QComboBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QComboBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommandLinkButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCommandLinkButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCommonStyle >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCommonStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCompleter::CompletionMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCompleter_CompletionMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCompleter::ModelSorting >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCompleter_ModelSorting_IDX]); }
template<> inline PyTypeObject *SbkType< ::QCompleter >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QCompleter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDataWidgetMapper::SubmitPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDataWidgetMapper_SubmitPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDataWidgetMapper >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDataWidgetMapper_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDateEdit >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDateEdit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDateTimeEdit::Section >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDateTimeEdit_Section_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QDateTimeEdit::Section> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QDateTimeEdit_Section_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDateTimeEdit >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDateTimeEdit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDial >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDial_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDialog::DialogCode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDialog_DialogCode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDialog >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDialogButtonBox::ButtonRole >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDialogButtonBox_ButtonRole_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDialogButtonBox::StandardButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDialogButtonBox_StandardButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QDialogButtonBox::StandardButton> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QDialogButtonBox_StandardButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDialogButtonBox::ButtonLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDialogButtonBox_ButtonLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDialogButtonBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDialogButtonBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDockWidget::DockWidgetFeature >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDockWidget_DockWidgetFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QDockWidget::DockWidgetFeature> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QDockWidget_DockWidgetFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDockWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDockWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QDoubleSpinBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QDoubleSpinBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QErrorMessage >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QErrorMessage_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDialog::ViewMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileDialog_ViewMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDialog::FileMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileDialog_FileMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDialog::AcceptMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileDialog_AcceptMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDialog::DialogLabel >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileDialog_DialogLabel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDialog::Option >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileDialog_Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QFileDialog::Option> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QFileDialog_Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileDialog >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileIconProvider >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileIconProvider_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileSystemModel::Roles >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileSystemModel_Roles_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileSystemModel::Option >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileSystemModel_Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QFileSystemModel::Option> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QFileSystemModel_Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFileSystemModel >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFileSystemModel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFocusFrame >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFocusFrame_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFontComboBox::FontFilter >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFontComboBox_FontFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QFontComboBox::FontFilter> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QFontComboBox_FontFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFontComboBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFontComboBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFontDialog::FontDialogOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFontDialog_FontDialogOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QFontDialog::FontDialogOption> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QFontDialog_FontDialogOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFontDialog >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFontDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFormLayout::FieldGrowthPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFormLayout_FieldGrowthPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFormLayout::RowWrapPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFormLayout_RowWrapPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFormLayout::ItemRole >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFormLayout_ItemRole_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFormLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFormLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFormLayout::TakeRowResult >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFormLayout_TakeRowResult_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFrame::Shape >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFrame_Shape_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFrame::Shadow >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFrame_Shadow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFrame::StyleMask >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFrame_StyleMask_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFrame >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFrame_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGesture::GestureCancelPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGesture_GestureCancelPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGesture >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGesture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGestureEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGestureEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGestureRecognizer::ResultFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGestureRecognizer_ResultFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGestureRecognizer::ResultFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QGestureRecognizer_ResultFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGestureRecognizer >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGestureRecognizer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsAnchor >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsAnchor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsAnchorLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsAnchorLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsBlurEffect::BlurHint >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsBlurEffect_BlurHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGraphicsBlurEffect::BlurHint> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QGraphicsBlurEffect_BlurHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsBlurEffect >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsBlurEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsColorizeEffect >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsColorizeEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsDropShadowEffect >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsDropShadowEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsEffect::ChangeFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsEffect_ChangeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGraphicsEffect::ChangeFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QGraphicsEffect_ChangeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsEffect::PixmapPadMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsEffect_PixmapPadMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsEffect >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsEllipseItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsEllipseItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsGridLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsGridLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsItem::GraphicsItemFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItem_GraphicsItemFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGraphicsItem::GraphicsItemFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QGraphicsItem_GraphicsItemFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsItem::GraphicsItemChange >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItem_GraphicsItemChange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsItem::CacheMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItem_CacheMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsItem::PanelModality >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItem_PanelModality_IDX]); }
template<> inline PyTypeObject *SbkType< ::PySide6_QtWidgets_QGraphicsItem_Extension_Surrogate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItem_Extension_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsItemAnimation >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItemAnimation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsItemGroup >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsItemGroup_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsLayoutItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsLayoutItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsLineItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsLineItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsLinearLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsLinearLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsObject >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsObject_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsOpacityEffect >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsOpacityEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsPathItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsPathItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsPixmapItem::ShapeMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsPixmapItem_ShapeMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsPixmapItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsPixmapItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsPolygonItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsPolygonItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsProxyWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsProxyWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsRectItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsRectItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsRotation >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsRotation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsScale >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsScale_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsScene::ItemIndexMethod >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsScene_ItemIndexMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsScene::SceneLayer >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsScene_SceneLayer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGraphicsScene::SceneLayer> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QGraphicsScene_SceneLayer_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsScene >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsScene_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneContextMenuEvent::Reason >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneContextMenuEvent_Reason_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneContextMenuEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneContextMenuEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneDragDropEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneDragDropEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneHelpEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneHelpEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneHoverEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneHoverEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneMouseEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneMouseEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneMoveEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneMoveEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneResizeEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneResizeEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSceneWheelEvent >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSceneWheelEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsSimpleTextItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsSimpleTextItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsTextItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsTextItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsTransform >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsTransform_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsView::ViewportAnchor >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsView_ViewportAnchor_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsView::CacheModeFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsView_CacheModeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGraphicsView::CacheModeFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QGraphicsView_CacheModeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsView::DragMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsView_DragMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsView::ViewportUpdateMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsView_ViewportUpdateMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsView::OptimizationFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsView_OptimizationFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QGraphicsView::OptimizationFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QGraphicsView_OptimizationFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGraphicsWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGraphicsWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGridLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGridLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QGroupBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QGroupBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHBoxLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QHBoxLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHeaderView::ResizeMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QHeaderView_ResizeMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QHeaderView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QHeaderView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QInputDialog::InputDialogOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QInputDialog_InputDialogOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QInputDialog::InputMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QInputDialog_InputMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QInputDialog >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QInputDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemDelegate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QItemDelegate_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemEditorCreatorBase >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QItemEditorCreatorBase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QItemEditorFactory >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QItemEditorFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QKeySequenceEdit >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QKeySequenceEdit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLCDNumber::Mode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLCDNumber_Mode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLCDNumber::SegmentStyle >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLCDNumber_SegmentStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLCDNumber >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLCDNumber_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLabel >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLabel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLayout::SizeConstraint >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLayout_SizeConstraint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLayoutItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLayoutItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineEdit::ActionPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLineEdit_ActionPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineEdit::EchoMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLineEdit_EchoMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QLineEdit >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QLineEdit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListView::Movement >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListView_Movement_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListView::Flow >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListView_Flow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListView::ResizeMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListView_ResizeMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListView::LayoutMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListView_LayoutMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListView::ViewMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListView_ViewMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListWidgetItem::ItemType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListWidgetItem_ItemType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QListWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QListWidgetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMainWindow::DockOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMainWindow_DockOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QMainWindow::DockOption> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QMainWindow_DockOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMainWindow >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMainWindow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMdiArea::AreaOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMdiArea_AreaOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QMdiArea::AreaOption> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QMdiArea_AreaOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMdiArea::WindowOrder >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMdiArea_WindowOrder_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMdiArea::ViewMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMdiArea_ViewMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMdiArea >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMdiArea_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMdiSubWindow::SubWindowOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMdiSubWindow_SubWindowOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QMdiSubWindow::SubWindowOption> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QMdiSubWindow_SubWindowOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMdiSubWindow >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMdiSubWindow_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMenu >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMenu_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMenuBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMenuBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageBox::Option >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMessageBox_Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QMessageBox::Option> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QMessageBox_Option_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageBox::Icon >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMessageBox_Icon_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageBox::ButtonRole >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMessageBox_ButtonRole_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageBox::StandardButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMessageBox_StandardButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QMessageBox::StandardButton> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QMessageBox_StandardButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QMessageBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QMessageBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPanGesture >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QPanGesture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPinchGesture::ChangeFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QPinchGesture_ChangeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QPinchGesture::ChangeFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QPinchGesture_ChangeFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPinchGesture >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QPinchGesture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlainTextDocumentLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QPlainTextDocumentLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlainTextEdit::LineWrapMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QPlainTextEdit_LineWrapMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPlainTextEdit >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QPlainTextEdit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProgressBar::Direction >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QProgressBar_Direction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProgressBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QProgressBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProgressDialog >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QProgressDialog_IDX]); }
template<> inline PyTypeObject *SbkType< ::QProxyStyle >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QProxyStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QPushButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QPushButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRadioButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QRadioButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRhiWidget::Api >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QRhiWidget_Api_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRhiWidget::TextureFormat >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QRhiWidget_TextureFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRhiWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QRhiWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRubberBand::Shape >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QRubberBand_Shape_IDX]); }
template<> inline PyTypeObject *SbkType< ::QRubberBand >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QRubberBand_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScrollArea >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScrollArea_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScrollBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScrollBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScroller::State >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScroller_State_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScroller::ScrollerGestureType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScroller_ScrollerGestureType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScroller::Input >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScroller_Input_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScroller >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScroller_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScrollerProperties::OvershootPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScrollerProperties_OvershootPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScrollerProperties::FrameRates >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScrollerProperties_FrameRates_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScrollerProperties::ScrollMetric >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScrollerProperties_ScrollMetric_IDX]); }
template<> inline PyTypeObject *SbkType< ::QScrollerProperties >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QScrollerProperties_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSizeGrip >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSizeGrip_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSizePolicy::PolicyFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSizePolicy_PolicyFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSizePolicy::Policy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSizePolicy_Policy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSizePolicy::ControlType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSizePolicy_ControlType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QSizePolicy::ControlType> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QSizePolicy_ControlType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSizePolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSizePolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSlider::TickPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSlider_TickPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSlider >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSlider_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSpacerItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSpacerItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSpinBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSpinBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSplashScreen >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSplashScreen_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSplitter >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSplitter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSplitterHandle >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSplitterHandle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStackedLayout::StackingMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStackedLayout_StackingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStackedLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStackedLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStackedWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStackedWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStatusBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStatusBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::StateFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_StateFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyle::StateFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyle_StateFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::PrimitiveElement >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_PrimitiveElement_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::ControlElement >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_ControlElement_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::SubElement >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_SubElement_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::ComplexControl >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_ComplexControl_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::SubControl >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_SubControl_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyle::SubControl> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyle_SubControl_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::PixelMetric >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_PixelMetric_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::ContentsType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_ContentsType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::RequestSoftwareInputPanel >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_RequestSoftwareInputPanel_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::StyleHint >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_StyleHint_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle::StandardPixmap >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_StandardPixmap_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyle >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleFactory >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleFactory_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturn::HintReturnType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturn_HintReturnType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturn::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturn_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturn::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturn_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturn >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturn_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturnMask::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturnMask_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturnMask::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturnMask_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturnMask >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturnMask_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturnVariant::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturnVariant_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturnVariant::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturnVariant_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleHintReturnVariant >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleHintReturnVariant_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOption::OptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOption_OptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOption::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOption_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOption::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOption_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionButton::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionButton_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionButton::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionButton_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionButton::ButtonFeature >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionButton_ButtonFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyleOptionButton::ButtonFeature> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyleOptionButton_ButtonFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionComboBox::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionComboBox_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionComboBox::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionComboBox_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionComboBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionComboBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionComplex::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionComplex_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionComplex::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionComplex_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionComplex >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionComplex_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionDockWidget::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionDockWidget_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionDockWidget::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionDockWidget_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionDockWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionDockWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionFocusRect::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionFocusRect_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionFocusRect::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionFocusRect_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionFocusRect >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionFocusRect_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionFrame::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionFrame_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionFrame::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionFrame_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionFrame::FrameFeature >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionFrame_FrameFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyleOptionFrame::FrameFeature> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyleOptionFrame_FrameFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionFrame >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionFrame_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionGraphicsItem::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionGraphicsItem_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionGraphicsItem::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionGraphicsItem_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionGraphicsItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionGraphicsItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionGroupBox::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionGroupBox_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionGroupBox::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionGroupBox_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionGroupBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionGroupBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeader::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeader_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeader::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeader_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeader::SectionPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeader_SectionPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeader::SelectedPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeader_SelectedPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeader::SortIndicator >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeader_SortIndicator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeader >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeader_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeaderV2::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeaderV2_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeaderV2::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeaderV2_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionHeaderV2 >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionHeaderV2_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionMenuItem::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionMenuItem_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionMenuItem::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionMenuItem_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionMenuItem::MenuItemType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionMenuItem_MenuItemType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionMenuItem::CheckType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionMenuItem_CheckType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionMenuItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionMenuItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionMenuItemV2::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionMenuItemV2_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionMenuItemV2 >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionMenuItemV2_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionProgressBar::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionProgressBar_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionProgressBar::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionProgressBar_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionProgressBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionProgressBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionRubberBand::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionRubberBand_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionRubberBand::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionRubberBand_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionRubberBand >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionRubberBand_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSizeGrip::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSizeGrip_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSizeGrip::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSizeGrip_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSizeGrip >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSizeGrip_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSlider::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSlider_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSlider::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSlider_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSlider >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSlider_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSpinBox::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSpinBox_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSpinBox::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSpinBox_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionSpinBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionSpinBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTab::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTab_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTab::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTab_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTab::TabPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTab_TabPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTab::SelectedPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTab_SelectedPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTab::CornerWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTab_CornerWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyleOptionTab::CornerWidget> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyleOptionTab_CornerWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTab::TabFeature >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTab_TabFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyleOptionTab::TabFeature> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyleOptionTab_TabFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTab >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTab_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTabBarBase::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTabBarBase_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTabBarBase::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTabBarBase_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTabBarBase >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTabBarBase_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTabWidgetFrame::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTabWidgetFrame_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTabWidgetFrame::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTabWidgetFrame_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTabWidgetFrame >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTabWidgetFrame_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTitleBar::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTitleBar_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTitleBar::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTitleBar_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionTitleBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionTitleBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBar::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBar_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBar::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBar_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBar::ToolBarPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBar_ToolBarPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBar::ToolBarFeature >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBar_ToolBarFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyleOptionToolBar::ToolBarFeature> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyleOptionToolBar_ToolBarFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBox::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBox_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBox::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBox_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBox::TabPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBox_TabPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBox::SelectedPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBox_SelectedPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolButton::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolButton_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolButton::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolButton_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolButton::ToolButtonFeature >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolButton_ToolButtonFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyleOptionToolButton::ToolButtonFeature> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyleOptionToolButton_ToolButtonFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionToolButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionToolButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionViewItem::StyleOptionType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionViewItem_StyleOptionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionViewItem::StyleOptionVersion >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionViewItem_StyleOptionVersion_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionViewItem::Position >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionViewItem_Position_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionViewItem::ViewItemFeature >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionViewItem_ViewItemFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QStyleOptionViewItem::ViewItemFeature> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QStyleOptionViewItem_ViewItemFeature_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionViewItem::ViewItemPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionViewItem_ViewItemPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyleOptionViewItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyleOptionViewItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStylePainter >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStylePainter_IDX]); }
template<> inline PyTypeObject *SbkType< ::QStyledItemDelegate >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QStyledItemDelegate_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSwipeGesture::SwipeDirection >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSwipeGesture_SwipeDirection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSwipeGesture >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSwipeGesture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSystemTrayIcon::ActivationReason >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSystemTrayIcon_ActivationReason_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSystemTrayIcon::MessageIcon >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSystemTrayIcon_MessageIcon_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSystemTrayIcon >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QSystemTrayIcon_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTabBar::Shape >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTabBar_Shape_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTabBar::ButtonPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTabBar_ButtonPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTabBar::SelectionBehavior >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTabBar_SelectionBehavior_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTabBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTabBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTabWidget::TabPosition >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTabWidget_TabPosition_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTabWidget::TabShape >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTabWidget_TabShape_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTabWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTabWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTableView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTableView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTableWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTableWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTableWidgetItem::ItemType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTableWidgetItem_ItemType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTableWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTableWidgetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTableWidgetSelectionRange >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTableWidgetSelectionRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTapAndHoldGesture >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTapAndHoldGesture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTapGesture >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTapGesture_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextBrowser >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTextBrowser_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextEdit::LineWrapMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTextEdit_LineWrapMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextEdit::AutoFormattingFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTextEdit_AutoFormattingFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QTextEdit::AutoFormattingFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QTextEdit_AutoFormattingFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextEdit >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTextEdit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTextEdit::ExtraSelection >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTextEdit_ExtraSelection_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTileRules >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTileRules_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTimeEdit >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTimeEdit_IDX]); }
template<> inline PyTypeObject *SbkType< ::QToolBar >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QToolBar_IDX]); }
template<> inline PyTypeObject *SbkType< ::QToolBox >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QToolBox_IDX]); }
template<> inline PyTypeObject *SbkType< ::QToolButton::ToolButtonPopupMode >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QToolButton_ToolButtonPopupMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::QToolButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QToolButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QToolTip >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QToolTip_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTreeView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTreeView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTreeWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTreeWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTreeWidgetItem::ItemType >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTreeWidgetItem_ItemType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTreeWidgetItem::ChildIndicatorPolicy >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTreeWidgetItem_ChildIndicatorPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTreeWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTreeWidgetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTreeWidgetItemIterator::IteratorFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTreeWidgetItemIterator_IteratorFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QTreeWidgetItemIterator::IteratorFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QTreeWidgetItemIterator_IteratorFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QTreeWidgetItemIterator >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QTreeWidgetItemIterator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QUndoView >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QUndoView_IDX]); }
template<> inline PyTypeObject *SbkType< ::QVBoxLayout >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QVBoxLayout_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWhatsThis >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWhatsThis_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWidget::RenderFlag >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWidget_RenderFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QWidget::RenderFlag> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QWidget_RenderFlag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWidget >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWidget_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWidgetAction >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWidgetAction_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWidgetItem >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWidgetItem_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWizard::WizardButton >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWizard_WizardButton_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWizard::WizardPixmap >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWizard_WizardPixmap_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWizard::WizardStyle >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWizard_WizardStyle_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWizard::WizardOption >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWizard_WizardOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<QWizard::WizardOption> >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QFlags_QWizard_WizardOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWizard >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWizard_IDX]); }
template<> inline PyTypeObject *SbkType< ::QWizardPage >() { return Shiboken::Module::get(SbkPySide6_QtWidgetsTypeStructs[SBK_QWizardPage_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QTWIDGETS_PYTHON_H

