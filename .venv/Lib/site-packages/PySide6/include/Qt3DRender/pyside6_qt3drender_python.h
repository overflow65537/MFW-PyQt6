// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QT3DRENDER_PYTHON_H
#define SBK_QT3DRENDER_PYTHON_H

#include <sbkpython.h>
#include <sbkmodule.h>
#include <sbkconverter.h>
// Module Includes
#include <pyside6_qt3dcore_python.h>
#include <pyside6_qtgui_python.h>
#include <pyside6_qtcore_python.h>
#include <pyside6_qtopengl_python.h>

// Bound library includes
#include <Qt3DRender/qabstractlight.h>
#include <Qt3DRender/qabstractraycaster.h>
#include <Qt3DRender/qabstracttexture.h>
#include <Qt3DRender/qalphatest.h>
#include <Qt3DRender/qblendequation.h>
#include <Qt3DRender/qblendequationarguments.h>
#include <Qt3DRender/qblitframebuffer.h>
#include <Qt3DRender/qcamera.h>
#include <Qt3DRender/qcameralens.h>
#include <Qt3DRender/qclearbuffers.h>
#include <Qt3DRender/qcomputecommand.h>
#include <Qt3DRender/qcullface.h>
#include <Qt3DRender/qdepthtest.h>
#include <Qt3DRender/qfrontface.h>
#include <Qt3DRender/qgeometryrenderer.h>
#include <Qt3DRender/qgraphicsapifilter.h>
#include <Qt3DRender/qlayerfilter.h>
#include <Qt3DRender/qlevelofdetail.h>
#include <Qt3DRender/qmemorybarrier.h>
#include <Qt3DRender/qmesh.h>
#include <Qt3DRender/qpickevent.h>
#include <Qt3DRender/qpickingsettings.h>
#include <Qt3DRender/qpointsize.h>
#include <Qt3DRender/qrastermode.h>
#include <Qt3DRender/qraycasterhit.h>
#include <Qt3DRender/qrenderapi.h>
#include <Qt3DRender/qrenderaspect.h>
#include <Qt3DRender/qrendercapabilities.h>
#include <Qt3DRender/qrendersettings.h>
#include <Qt3DRender/qrendertargetoutput.h>
#include <Qt3DRender/qsceneloader.h>
#include <Qt3DRender/qsetfence.h>
#include <Qt3DRender/qshaderimage.h>
#include <Qt3DRender/qshaderprogram.h>
#include <Qt3DRender/qsortpolicy.h>
#include <Qt3DRender/qstenciloperationarguments.h>
#include <Qt3DRender/qstenciltestarguments.h>
#include <Qt3DRender/qsubtreeenabler.h>
#include <Qt3DRender/qtextureimage.h>
#include <Qt3DRender/qtexturewrapmode.h>
#include <Qt3DRender/qwaitfence.h>
#include <qsharedpointer.h>

QT_BEGIN_NAMESPACE

namespace Qt3DRender {
    class PropertyReaderInterface;
    class QAbstractTextureImage;
    class QAlphaCoverage;
    class QBufferCapture;
    class QCameraSelector;
    class QClipPlane;
    class QColorMask;
    class QDebugOverlay;
    class QDepthRange;
    class QDirectionalLight;
    class QDispatchCompute;
    class QDithering;
    class QEffect;
    class QEnvironmentLight;
    class QFilterKey;
    class QFrameGraphNode;
    class QFrustumCulling;
    class QLayer;
    class QLevelOfDetailBoundingSphere;
    class QLevelOfDetailSwitch;
    class QLineWidth;
    class QMaterial;
    class QMultiSampleAntiAliasing;
    class QNoDepthMask;
    class QNoDraw;
    class QNoPicking;
    class QObjectPicker;
    class QPaintedTextureImage;
    class QParameter;
    class QPickLineEvent;
    class QPickPointEvent;
    class QPickTriangleEvent;
    class QPickingProxy;
    class QPointLight;
    class QPolygonOffset;
    class QProximityFilter;
    class QRayCaster;
    class QRenderCapture;
    class QRenderCaptureReply;
    class QRenderPass;
    class QRenderPassFilter;
    class QRenderState;
    class QRenderStateSet;
    class QRenderSurfaceSelector;
    class QRenderTarget;
    class QRenderTargetSelector;
    class QScissorTest;
    class QScreenRayCaster;
    class QSeamlessCubemap;
    class QShaderData;
    class QShaderProgramBuilder;
    class QSharedGLTexture;
    class QSpotLight;
    class QStencilMask;
    class QStencilOperation;
    class QStencilTest;
    class QTechnique;
    class QTechniqueFilter;
    class QTexture1D;
    class QTexture1DArray;
    class QTexture2D;
    class QTexture2DArray;
    class QTexture2DMultisample;
    class QTexture2DMultisampleArray;
    class QTexture3D;
    class QTextureBuffer;
    class QTextureCubeMap;
    class QTextureCubeMapArray;
    class QTextureData;
    class QTextureDataUpdate;
    class QTextureImageData;
    class QTextureImageDataGenerator;
    class QTextureLoader;
    class QTextureRectangle;
    class QViewport;
}
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_Qt3DRender_API_IDX                                   = 4,
    SBK_Qt3DRenderQt3DRender_IDX                             = 3,
    SBK_Qt3DRender_PropertyReaderInterface_IDX               = 5,
    SBK_Qt3DRender_QAbstractLight_Type_IDX                   = 7,
    SBK_Qt3DRender_QAbstractLight_IDX                        = 6,
    SBK_Qt3DRender_QAbstractRayCaster_RunMode_IDX            = 10,
    SBK_Qt3DRender_QAbstractRayCaster_FilterMode_IDX         = 9,
    SBK_Qt3DRender_QAbstractRayCaster_IDX                    = 8,
    SBK_Qt3DRender_QAbstractTexture_Status_IDX               = 17,
    SBK_Qt3DRender_QAbstractTexture_Target_IDX               = 18,
    SBK_Qt3DRender_QAbstractTexture_TextureFormat_IDX        = 19,
    SBK_Qt3DRender_QAbstractTexture_Filter_IDX               = 15,
    SBK_Qt3DRender_QAbstractTexture_CubeMapFace_IDX          = 14,
    SBK_Qt3DRender_QAbstractTexture_ComparisonFunction_IDX   = 12,
    SBK_Qt3DRender_QAbstractTexture_ComparisonMode_IDX       = 13,
    SBK_Qt3DRender_QAbstractTexture_HandleType_IDX           = 16,
    SBK_Qt3DRender_QAbstractTexture_IDX                      = 11,
    SBK_Qt3DRender_QAbstractTextureImage_IDX                 = 20,
    SBK_Qt3DRender_QAlphaCoverage_IDX                        = 21,
    SBK_Qt3DRender_QAlphaTest_AlphaFunction_IDX              = 23,
    SBK_Qt3DRender_QAlphaTest_IDX                            = 22,
    SBK_Qt3DRender_QBlendEquation_BlendFunction_IDX          = 25,
    SBK_Qt3DRender_QBlendEquation_IDX                        = 24,
    SBK_Qt3DRender_QBlendEquationArguments_Blending_IDX      = 27,
    SBK_Qt3DRender_QBlendEquationArguments_IDX               = 26,
    SBK_Qt3DRender_QBlitFramebuffer_InterpolationMethod_IDX  = 29,
    SBK_Qt3DRender_QBlitFramebuffer_IDX                      = 28,
    SBK_Qt3DRender_QBufferCapture_IDX                        = 30,
    SBK_Qt3DRender_QCamera_CameraTranslationOption_IDX       = 32,
    SBK_Qt3DRender_QCamera_IDX                               = 31,
    SBK_Qt3DRender_QCameraLens_ProjectionType_IDX            = 34,
    SBK_Qt3DRender_QCameraLens_IDX                           = 33,
    SBK_Qt3DRender_QCameraSelector_IDX                       = 35,
    SBK_Qt3DRender_QClearBuffers_BufferType_IDX              = 37,
    SBK_QFlags_Qt3DRender_QClearBuffers_BufferType_IDX       = 0,
    SBK_Qt3DRender_QClearBuffers_IDX                         = 36,
    SBK_Qt3DRender_QClipPlane_IDX                            = 38,
    SBK_Qt3DRender_QColorMask_IDX                            = 39,
    SBK_Qt3DRender_QComputeCommand_RunType_IDX               = 41,
    SBK_Qt3DRender_QComputeCommand_IDX                       = 40,
    SBK_Qt3DRender_QCullFace_CullingMode_IDX                 = 43,
    SBK_Qt3DRender_QCullFace_IDX                             = 42,
    SBK_Qt3DRender_QDebugOverlay_IDX                         = 44,
    SBK_Qt3DRender_QDepthRange_IDX                           = 45,
    SBK_Qt3DRender_QDepthTest_DepthFunction_IDX              = 47,
    SBK_Qt3DRender_QDepthTest_IDX                            = 46,
    SBK_Qt3DRender_QDirectionalLight_IDX                     = 48,
    SBK_Qt3DRender_QDispatchCompute_IDX                      = 49,
    SBK_Qt3DRender_QDithering_IDX                            = 50,
    SBK_Qt3DRender_QEffect_IDX                               = 51,
    SBK_Qt3DRender_QEnvironmentLight_IDX                     = 52,
    SBK_Qt3DRender_QFilterKey_IDX                            = 53,
    SBK_Qt3DRender_QFrameGraphNode_IDX                       = 54,
    SBK_Qt3DRender_QFrontFace_WindingDirection_IDX           = 56,
    SBK_Qt3DRender_QFrontFace_IDX                            = 55,
    SBK_Qt3DRender_QFrustumCulling_IDX                       = 57,
    SBK_Qt3DRender_QGeometryRenderer_PrimitiveType_IDX       = 59,
    SBK_Qt3DRender_QGeometryRenderer_IDX                     = 58,
    SBK_Qt3DRender_QGraphicsApiFilter_Api_IDX                = 61,
    SBK_Qt3DRender_QGraphicsApiFilter_OpenGLProfile_IDX      = 62,
    SBK_Qt3DRender_QGraphicsApiFilter_IDX                    = 60,
    SBK_Qt3DRender_QLayer_IDX                                = 63,
    SBK_Qt3DRender_QLayerFilter_FilterMode_IDX               = 65,
    SBK_Qt3DRender_QLayerFilter_IDX                          = 64,
    SBK_Qt3DRender_QLevelOfDetail_ThresholdType_IDX          = 67,
    SBK_Qt3DRender_QLevelOfDetail_IDX                        = 66,
    SBK_Qt3DRender_QLevelOfDetailBoundingSphere_IDX          = 68,
    SBK_Qt3DRender_QLevelOfDetailSwitch_IDX                  = 69,
    SBK_Qt3DRender_QLineWidth_IDX                            = 70,
    SBK_Qt3DRender_QMaterial_IDX                             = 71,
    SBK_Qt3DRender_QMemoryBarrier_Operation_IDX              = 73,
    SBK_QFlags_Qt3DRender_QMemoryBarrier_Operation_IDX       = 1,
    SBK_Qt3DRender_QMemoryBarrier_IDX                        = 72,
    SBK_Qt3DRender_QMesh_Status_IDX                          = 75,
    SBK_Qt3DRender_QMesh_IDX                                 = 74,
    SBK_Qt3DRender_QMultiSampleAntiAliasing_IDX              = 76,
    SBK_Qt3DRender_QNoDepthMask_IDX                          = 77,
    SBK_Qt3DRender_QNoDraw_IDX                               = 78,
    SBK_Qt3DRender_QNoPicking_IDX                            = 79,
    SBK_Qt3DRender_QObjectPicker_IDX                         = 80,
    SBK_Qt3DRender_QPaintedTextureImage_IDX                  = 81,
    SBK_Qt3DRender_QParameter_IDX                            = 82,
    SBK_Qt3DRender_QPickEvent_Buttons_IDX                    = 84,
    SBK_Qt3DRender_QPickEvent_Modifiers_IDX                  = 85,
    SBK_Qt3DRender_QPickEvent_IDX                            = 83,
    SBK_Qt3DRender_QPickLineEvent_IDX                        = 86,
    SBK_Qt3DRender_QPickPointEvent_IDX                       = 87,
    SBK_Qt3DRender_QPickTriangleEvent_IDX                    = 88,
    SBK_Qt3DRender_QPickingProxy_IDX                         = 89,
    SBK_Qt3DRender_QPickingSettings_PickMethod_IDX           = 92,
    SBK_Qt3DRender_QPickingSettings_PickResultMode_IDX       = 93,
    SBK_Qt3DRender_QPickingSettings_FaceOrientationPickingMode_IDX = 91,
    SBK_Qt3DRender_QPickingSettings_IDX                      = 90,
    SBK_Qt3DRender_QPointLight_IDX                           = 94,
    SBK_Qt3DRender_QPointSize_SizeMode_IDX                   = 96,
    SBK_Qt3DRender_QPointSize_IDX                            = 95,
    SBK_Qt3DRender_QPolygonOffset_IDX                        = 97,
    SBK_Qt3DRender_QProximityFilter_IDX                      = 98,
    SBK_Qt3DRender_QRasterMode_RasterMode_IDX                = 101,
    SBK_Qt3DRender_QRasterMode_FaceMode_IDX                  = 100,
    SBK_Qt3DRender_QRasterMode_IDX                           = 99,
    SBK_Qt3DRender_QRayCaster_IDX                            = 102,
    SBK_Qt3DRender_QRayCasterHit_HitType_IDX                 = 104,
    SBK_Qt3DRender_QRayCasterHit_IDX                         = 103,
    SBK_Qt3DRender_QRenderAspect_SubmissionType_IDX          = 106,
    SBK_Qt3DRender_QRenderAspect_IDX                         = 105,
    SBK_Qt3DRender_QRenderCapabilities_API_IDX               = 108,
    SBK_Qt3DRender_QRenderCapabilities_Profile_IDX           = 109,
    SBK_Qt3DRender_QRenderCapabilities_IDX                   = 107,
    SBK_Qt3DRender_QRenderCapture_IDX                        = 110,
    SBK_Qt3DRender_QRenderCaptureReply_IDX                   = 111,
    SBK_Qt3DRender_QRenderPass_IDX                           = 112,
    SBK_Qt3DRender_QRenderPassFilter_IDX                     = 113,
    SBK_Qt3DRender_QRenderSettings_RenderPolicy_IDX          = 115,
    SBK_Qt3DRender_QRenderSettings_IDX                       = 114,
    SBK_Qt3DRender_QRenderState_IDX                          = 116,
    SBK_Qt3DRender_QRenderStateSet_IDX                       = 117,
    SBK_Qt3DRender_QRenderSurfaceSelector_IDX                = 118,
    SBK_Qt3DRender_QRenderTarget_IDX                         = 119,
    SBK_Qt3DRender_QRenderTargetOutput_AttachmentPoint_IDX   = 121,
    SBK_Qt3DRender_QRenderTargetOutput_IDX                   = 120,
    SBK_Qt3DRender_QRenderTargetSelector_IDX                 = 122,
    SBK_Qt3DRender_QSceneLoader_Status_IDX                   = 125,
    SBK_Qt3DRender_QSceneLoader_ComponentType_IDX            = 124,
    SBK_Qt3DRender_QSceneLoader_IDX                          = 123,
    SBK_Qt3DRender_QScissorTest_IDX                          = 126,
    SBK_Qt3DRender_QScreenRayCaster_IDX                      = 127,
    SBK_Qt3DRender_QSeamlessCubemap_IDX                      = 128,
    SBK_Qt3DRender_QSetFence_HandleType_IDX                  = 130,
    SBK_Qt3DRender_QSetFence_IDX                             = 129,
    SBK_Qt3DRender_QShaderData_IDX                           = 131,
    SBK_Qt3DRender_QShaderImage_Access_IDX                   = 133,
    SBK_Qt3DRender_QShaderImage_ImageFormat_IDX              = 134,
    SBK_Qt3DRender_QShaderImage_IDX                          = 132,
    SBK_Qt3DRender_QShaderProgram_ShaderType_IDX             = 137,
    SBK_Qt3DRender_QShaderProgram_Status_IDX                 = 138,
    SBK_Qt3DRender_QShaderProgram_Format_IDX                 = 136,
    SBK_Qt3DRender_QShaderProgram_IDX                        = 135,
    SBK_Qt3DRender_QShaderProgramBuilder_IDX                 = 139,
    SBK_Qt3DRender_QSharedGLTexture_IDX                      = 140,
    SBK_Qt3DRender_QSortPolicy_SortType_IDX                  = 142,
    SBK_Qt3DRender_QSortPolicy_IDX                           = 141,
    SBK_Qt3DRender_QSpotLight_IDX                            = 143,
    SBK_Qt3DRender_QStencilMask_IDX                          = 144,
    SBK_Qt3DRender_QStencilOperation_IDX                     = 145,
    SBK_Qt3DRender_QStencilOperationArguments_FaceMode_IDX   = 147,
    SBK_Qt3DRender_QStencilOperationArguments_Operation_IDX  = 148,
    SBK_Qt3DRender_QStencilOperationArguments_IDX            = 146,
    SBK_Qt3DRender_QStencilTest_IDX                          = 149,
    SBK_Qt3DRender_QStencilTestArguments_StencilFaceMode_IDX = 151,
    SBK_Qt3DRender_QStencilTestArguments_StencilFunction_IDX = 152,
    SBK_Qt3DRender_QStencilTestArguments_IDX                 = 150,
    SBK_Qt3DRender_QSubtreeEnabler_Enablement_IDX            = 154,
    SBK_Qt3DRender_QSubtreeEnabler_IDX                       = 153,
    SBK_Qt3DRender_QTechnique_IDX                            = 155,
    SBK_Qt3DRender_QTechniqueFilter_IDX                      = 156,
    SBK_Qt3DRender_QTexture1D_IDX                            = 157,
    SBK_Qt3DRender_QTexture1DArray_IDX                       = 158,
    SBK_Qt3DRender_QTexture2D_IDX                            = 159,
    SBK_Qt3DRender_QTexture2DArray_IDX                       = 160,
    SBK_Qt3DRender_QTexture2DMultisample_IDX                 = 161,
    SBK_Qt3DRender_QTexture2DMultisampleArray_IDX            = 162,
    SBK_Qt3DRender_QTexture3D_IDX                            = 163,
    SBK_Qt3DRender_QTextureBuffer_IDX                        = 164,
    SBK_Qt3DRender_QTextureCubeMap_IDX                       = 165,
    SBK_Qt3DRender_QTextureCubeMapArray_IDX                  = 166,
    SBK_Qt3DRender_QTextureData_IDX                          = 167,
    SBK_Qt3DRender_QTextureDataUpdate_IDX                    = 168,
    SBK_Qt3DRender_QTextureImage_Status_IDX                  = 170,
    SBK_Qt3DRender_QTextureImage_IDX                         = 169,
    SBK_Qt3DRender_QTextureImageData_IDX                     = 171,
    SBK_Qt3DRender_QTextureImageDataGenerator_IDX            = 172,
    SBK_Qt3DRender_QTextureLoader_IDX                        = 173,
    SBK_Qt3DRender_QTextureRectangle_IDX                     = 174,
    SBK_Qt3DRender_QTextureWrapMode_WrapMode_IDX             = 176,
    SBK_Qt3DRender_QTextureWrapMode_IDX                      = 175,
    SBK_Qt3DRender_QViewport_IDX                             = 177,
    SBK_Qt3DRender_QWaitFence_HandleType_IDX                 = 179,
    SBK_Qt3DRender_QWaitFence_IDX                            = 178,
    SBK_QSharedPointer_Qt3DRender_PropertyReaderInterface_IDX = 180, // QSharedPointer<Qt3DRender::PropertyReaderInterface>
    SBK_QSharedPointer_constQt3DRender_PropertyReaderInterface_IDX = 180, // (const)
    SBK_QSharedPointer_Qt3DRender_QTextureImageDataGenerator_IDX = 181, // QSharedPointer<Qt3DRender::QTextureImageDataGenerator>
    SBK_QSharedPointer_constQt3DRender_QTextureImageDataGenerator_IDX = 181, // (const)
    SBK_QSharedPointer_Qt3DRender_QTextureImageData_IDX      = 182, // QSharedPointer<Qt3DRender::QTextureImageData>
    SBK_QSharedPointer_constQt3DRender_QTextureImageData_IDX = 182, // (const)
    SBK_Qt3DRender_IDX_COUNT                                 = 183,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_Qt3DRenderTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_Qt3DRenderModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_Qt3DRenderTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QT3DRENDER_QLIST_INT_IDX                             = 0, // QList<int>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QRAYCASTERHIT_IDX        = 1, // QList<Qt3DRender::QRayCasterHit>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QLAYERPTR_IDX            = 2, // QList<Qt3DRender::QLayer*>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QABSTRACTTEXTUREIMAGEPTR_IDX = 3, // QList<Qt3DRender::QAbstractTextureImage*>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QFILTERKEYPTR_IDX        = 4, // QList<Qt3DRender::QFilterKey*>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QPARAMETERPTR_IDX        = 5, // QList<Qt3DRender::QParameter*>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QRENDERSTATEPTR_IDX      = 6, // QList<Qt3DRender::QRenderState*>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QSORTPOLICY_SORTTYPE_IDX = 7, // QList<Qt3DRender::QSortPolicy::SortType>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QRENDERTARGETOUTPUTPTR_IDX = 8, // QList<Qt3DRender::QRenderTargetOutput*>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QTECHNIQUEPTR_IDX        = 9, // QList<Qt3DRender::QTechnique*>
    SBK_QT3DRENDER_QLIST_QREAL_IDX                           = 10, // QList<qreal>
    SBK_QT3DRENDER_STD_VECTOR_QSHAREDPOINTER_QT3DCORE_QASPECTJOB_IDX = 11, // std::vector<QSharedPointer<Qt3DCore::QAspectJob>>
    SBK_QT3DRENDER_QLIST_QT3DRENDER_QRENDERPASSPTR_IDX       = 12, // QList<Qt3DRender::QRenderPass*>
    SBK_QT3DRENDER_QLIST_QSHAREDPOINTER_QT3DRENDER_QTEXTUREIMAGEDATA_IDX = 13, // QList<QSharedPointer<Qt3DRender::QTextureImageData>>
    SBK_QT3DRENDER_QLIST_QVARIANT_IDX                        = 14, // QList<QVariant>
    SBK_QT3DRENDER_QLIST_QSTRING_IDX                         = 15, // QList<QString>
    SBK_QT3DRENDER_QMAP_QSTRING_QVARIANT_IDX                 = 16, // QMap<QString,QVariant>
    SBK_QT3DRENDER_CONVERTERS_IDX_COUNT                      = 17,
};

// Converter indices
enum : int {
    SBK_Qt3DRender_QList_int_IDX                             = 0, // QList<int>
    SBK_Qt3DRender_QList_Qt3DRender_QRayCasterHit_IDX        = 1, // QList<Qt3DRender::QRayCasterHit>
    SBK_Qt3DRender_QList_Qt3DRender_QLayerPTR_IDX            = 2, // QList<Qt3DRender::QLayer*>
    SBK_Qt3DRender_QList_Qt3DRender_QAbstractTextureImagePTR_IDX = 3, // QList<Qt3DRender::QAbstractTextureImage*>
    SBK_Qt3DRender_QList_Qt3DRender_QFilterKeyPTR_IDX        = 4, // QList<Qt3DRender::QFilterKey*>
    SBK_Qt3DRender_QList_Qt3DRender_QParameterPTR_IDX        = 5, // QList<Qt3DRender::QParameter*>
    SBK_Qt3DRender_QList_Qt3DRender_QRenderStatePTR_IDX      = 6, // QList<Qt3DRender::QRenderState*>
    SBK_Qt3DRender_QList_Qt3DRender_QSortPolicy_SortType_IDX = 7, // QList<Qt3DRender::QSortPolicy::SortType>
    SBK_Qt3DRender_QList_Qt3DRender_QRenderTargetOutputPTR_IDX = 8, // QList<Qt3DRender::QRenderTargetOutput*>
    SBK_Qt3DRender_QList_Qt3DRender_QTechniquePTR_IDX        = 9, // QList<Qt3DRender::QTechnique*>
    SBK_Qt3DRender_QList_qreal_IDX                           = 10, // QList<qreal>
    SBK_Qt3DRender_std_vector_QSharedPointer_Qt3DCore_QAspectJob_IDX = 11, // std::vector<QSharedPointer<Qt3DCore::QAspectJob>>
    SBK_Qt3DRender_QList_Qt3DRender_QRenderPassPTR_IDX       = 12, // QList<Qt3DRender::QRenderPass*>
    SBK_Qt3DRender_QList_QSharedPointer_Qt3DRender_QTextureImageData_IDX = 13, // QList<QSharedPointer<Qt3DRender::QTextureImageData>>
    SBK_Qt3DRender_QList_QVariant_IDX                        = 14, // QList<QVariant>
    SBK_Qt3DRender_QList_QString_IDX                         = 15, // QList<QString>
    SBK_Qt3DRender_QMap_QString_QVariant_IDX                 = 16, // QMap<QString,QVariant>
    SBK_Qt3DRender_CONVERTERS_IDX_COUNT                      = 17,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::Qt3DRender::API >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_API_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::PropertyReaderInterface >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_PropertyReaderInterface_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractLight::Type >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractLight_Type_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractLight >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractLight_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractRayCaster::RunMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractRayCaster_RunMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractRayCaster::FilterMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractRayCaster_FilterMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractRayCaster >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractRayCaster_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::Status >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::Target >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_Target_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::TextureFormat >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_TextureFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::Filter >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_Filter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::CubeMapFace >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_CubeMapFace_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::ComparisonFunction >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_ComparisonFunction_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::ComparisonMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_ComparisonMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture::HandleType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_HandleType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTexture >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTexture_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAbstractTextureImage >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAbstractTextureImage_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAlphaCoverage >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAlphaCoverage_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAlphaTest::AlphaFunction >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAlphaTest_AlphaFunction_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QAlphaTest >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QAlphaTest_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QBlendEquation::BlendFunction >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QBlendEquation_BlendFunction_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QBlendEquation >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QBlendEquation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QBlendEquationArguments::Blending >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QBlendEquationArguments_Blending_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QBlendEquationArguments >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QBlendEquationArguments_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QBlitFramebuffer::InterpolationMethod >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QBlitFramebuffer_InterpolationMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QBlitFramebuffer >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QBlitFramebuffer_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QBufferCapture >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QBufferCapture_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QCamera::CameraTranslationOption >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QCamera_CameraTranslationOption_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QCamera >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QCamera_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QCameraLens::ProjectionType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QCameraLens_ProjectionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QCameraLens >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QCameraLens_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QCameraSelector >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QCameraSelector_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QClearBuffers::BufferType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QClearBuffers_BufferType_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt3DRender::QClearBuffers::BufferType> >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_QFlags_Qt3DRender_QClearBuffers_BufferType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QClearBuffers >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QClearBuffers_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QClipPlane >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QClipPlane_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QColorMask >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QColorMask_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QComputeCommand::RunType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QComputeCommand_RunType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QComputeCommand >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QComputeCommand_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QCullFace::CullingMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QCullFace_CullingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QCullFace >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QCullFace_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QDebugOverlay >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QDebugOverlay_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QDepthRange >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QDepthRange_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QDepthTest::DepthFunction >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QDepthTest_DepthFunction_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QDepthTest >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QDepthTest_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QDirectionalLight >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QDirectionalLight_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QDispatchCompute >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QDispatchCompute_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QDithering >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QDithering_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QEffect >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QEffect_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QEnvironmentLight >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QEnvironmentLight_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QFilterKey >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QFilterKey_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QFrameGraphNode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QFrameGraphNode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QFrontFace::WindingDirection >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QFrontFace_WindingDirection_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QFrontFace >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QFrontFace_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QFrustumCulling >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QFrustumCulling_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QGeometryRenderer::PrimitiveType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QGeometryRenderer_PrimitiveType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QGeometryRenderer >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QGeometryRenderer_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QGraphicsApiFilter::Api >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QGraphicsApiFilter_Api_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QGraphicsApiFilter::OpenGLProfile >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QGraphicsApiFilter_OpenGLProfile_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QGraphicsApiFilter >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QGraphicsApiFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLayer >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLayer_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLayerFilter::FilterMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLayerFilter_FilterMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLayerFilter >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLayerFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLevelOfDetail::ThresholdType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLevelOfDetail_ThresholdType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLevelOfDetail >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLevelOfDetail_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLevelOfDetailBoundingSphere >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLevelOfDetailBoundingSphere_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLevelOfDetailSwitch >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLevelOfDetailSwitch_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QLineWidth >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QLineWidth_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QMaterial >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QMaterial_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QMemoryBarrier::Operation >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QMemoryBarrier_Operation_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt3DRender::QMemoryBarrier::Operation> >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_QFlags_Qt3DRender_QMemoryBarrier_Operation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QMemoryBarrier >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QMemoryBarrier_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QMesh::Status >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QMesh_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QMesh >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QMesh_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QMultiSampleAntiAliasing >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QMultiSampleAntiAliasing_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QNoDepthMask >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QNoDepthMask_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QNoDraw >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QNoDraw_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QNoPicking >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QNoPicking_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QObjectPicker >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QObjectPicker_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPaintedTextureImage >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPaintedTextureImage_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QParameter >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QParameter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickEvent::Buttons >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickEvent_Buttons_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickEvent::Modifiers >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickEvent_Modifiers_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickEvent >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickLineEvent >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickLineEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickPointEvent >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickPointEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickTriangleEvent >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickTriangleEvent_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickingProxy >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickingProxy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickingSettings::PickMethod >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickingSettings_PickMethod_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickingSettings::PickResultMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickingSettings_PickResultMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickingSettings::FaceOrientationPickingMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickingSettings_FaceOrientationPickingMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPickingSettings >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPickingSettings_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPointLight >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPointLight_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPointSize::SizeMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPointSize_SizeMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPointSize >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPointSize_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QPolygonOffset >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QPolygonOffset_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QProximityFilter >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QProximityFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRasterMode::RasterMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRasterMode_RasterMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRasterMode::FaceMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRasterMode_FaceMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRasterMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRasterMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRayCaster >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRayCaster_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRayCasterHit::HitType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRayCasterHit_HitType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRayCasterHit >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRayCasterHit_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderAspect::SubmissionType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderAspect_SubmissionType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderAspect >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderAspect_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderCapabilities::API >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderCapabilities_API_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderCapabilities::Profile >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderCapabilities_Profile_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderCapabilities >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderCapabilities_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderCapture >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderCapture_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderCaptureReply >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderCaptureReply_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderPass >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderPass_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderPassFilter >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderPassFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderSettings::RenderPolicy >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderSettings_RenderPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderSettings >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderSettings_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderState >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderState_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderStateSet >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderStateSet_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderSurfaceSelector >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderSurfaceSelector_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderTarget >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderTarget_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderTargetOutput::AttachmentPoint >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderTargetOutput_AttachmentPoint_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderTargetOutput >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderTargetOutput_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QRenderTargetSelector >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QRenderTargetSelector_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSceneLoader::Status >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSceneLoader_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSceneLoader::ComponentType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSceneLoader_ComponentType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSceneLoader >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSceneLoader_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QScissorTest >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QScissorTest_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QScreenRayCaster >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QScreenRayCaster_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSeamlessCubemap >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSeamlessCubemap_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSetFence::HandleType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSetFence_HandleType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSetFence >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSetFence_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderData >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderData_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderImage::Access >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderImage_Access_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderImage::ImageFormat >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderImage_ImageFormat_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderImage >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderImage_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderProgram::ShaderType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderProgram_ShaderType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderProgram::Status >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderProgram_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderProgram::Format >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderProgram_Format_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderProgram >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderProgram_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QShaderProgramBuilder >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QShaderProgramBuilder_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSharedGLTexture >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSharedGLTexture_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSortPolicy::SortType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSortPolicy_SortType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSortPolicy >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSortPolicy_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSpotLight >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSpotLight_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilMask >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilMask_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilOperation >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilOperation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilOperationArguments::FaceMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilOperationArguments_FaceMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilOperationArguments::Operation >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilOperationArguments_Operation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilOperationArguments >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilOperationArguments_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilTest >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilTest_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilTestArguments::StencilFaceMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilTestArguments_StencilFaceMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilTestArguments::StencilFunction >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilTestArguments_StencilFunction_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QStencilTestArguments >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QStencilTestArguments_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSubtreeEnabler::Enablement >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSubtreeEnabler_Enablement_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QSubtreeEnabler >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QSubtreeEnabler_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTechnique >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTechnique_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTechniqueFilter >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTechniqueFilter_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTexture1D >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTexture1D_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTexture1DArray >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTexture1DArray_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTexture2D >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTexture2D_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTexture2DArray >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTexture2DArray_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTexture2DMultisample >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTexture2DMultisample_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTexture2DMultisampleArray >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTexture2DMultisampleArray_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTexture3D >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTexture3D_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureBuffer >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureBuffer_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureCubeMap >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureCubeMap_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureCubeMapArray >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureCubeMapArray_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureData >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureData_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureDataUpdate >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureDataUpdate_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureImage::Status >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureImage_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureImage >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureImage_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureImageData >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureImageData_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureImageDataGenerator >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureImageDataGenerator_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureLoader >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureLoader_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureRectangle >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureRectangle_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureWrapMode::WrapMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureWrapMode_WrapMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QTextureWrapMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QTextureWrapMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QViewport >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QViewport_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QWaitFence::HandleType >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QWaitFence_HandleType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DRender::QWaitFence >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_Qt3DRender_QWaitFence_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSharedPointer<Qt3DRender::PropertyReaderInterface> >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_QSharedPointer_Qt3DRender_PropertyReaderInterface_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSharedPointer<Qt3DRender::QTextureImageDataGenerator> >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_QSharedPointer_Qt3DRender_QTextureImageDataGenerator_IDX]); }
template<> inline PyTypeObject *SbkType< ::QSharedPointer<Qt3DRender::QTextureImageData> >() { return Shiboken::Module::get(SbkPySide6_Qt3DRenderTypeStructs[SBK_QSharedPointer_Qt3DRender_QTextureImageData_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QT3DRENDER_PYTHON_H

