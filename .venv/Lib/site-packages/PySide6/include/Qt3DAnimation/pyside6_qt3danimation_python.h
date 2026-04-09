// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only


#ifndef SBK_QT3DANIMATION_PYTHON_H
#define SBK_QT3DANIMATION_PYTHON_H

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
#include <Qt3DAnimation/qabstractanimation.h>
#include <Qt3DAnimation/qabstractclipanimator.h>
#include <Qt3DAnimation/qanimationcallback.h>
#include <Qt3DAnimation/qanimationcliploader.h>
#include <Qt3DAnimation/qkeyframe.h>
#include <Qt3DAnimation/qkeyframeanimation.h>
#include <Qt3DAnimation/qmorphinganimation.h>

QT_BEGIN_NAMESPACE

namespace Qt3DAnimation {
    class QAbstractAnimationClip;
    class QAbstractChannelMapping;
    class QAbstractClipBlendNode;
    class QAdditiveClipBlend;
    class QAnimationAspect;
    class QAnimationClip;
    class QAnimationClipData;
    class QAnimationController;
    class QAnimationGroup;
    class QBlendedClipAnimator;
    class QCallbackMapping;
    class QChannel;
    class QChannelComponent;
    class QChannelMapper;
    class QChannelMapping;
    class QClipAnimator;
    class QClipBlendValue;
    class QClock;
    class QLerpClipBlend;
    class QMorphTarget;
    class QSkeletonMapping;
    class QVertexBlendAnimation;
}
QT_END_NAMESPACE

// Type indices
enum : int {
    SBK_Qt3DAnimationQt3DAnimation_IDX                       = 1,
    SBK_Qt3DAnimation_QAbstractAnimation_AnimationType_IDX   = 3,
    SBK_Qt3DAnimation_QAbstractAnimation_IDX                 = 2,
    SBK_Qt3DAnimation_QAbstractAnimationClip_IDX             = 4,
    SBK_Qt3DAnimation_QAbstractChannelMapping_IDX            = 5,
    SBK_Qt3DAnimation_QAbstractClipAnimator_Loops_IDX        = 7,
    SBK_Qt3DAnimation_QAbstractClipAnimator_IDX              = 6,
    SBK_Qt3DAnimation_QAbstractClipBlendNode_IDX             = 8,
    SBK_Qt3DAnimation_QAdditiveClipBlend_IDX                 = 9,
    SBK_Qt3DAnimation_QAnimationAspect_IDX                   = 10,
    SBK_Qt3DAnimation_QAnimationCallback_Flag_IDX            = 12,
    SBK_QFlags_Qt3DAnimation_QAnimationCallback_Flag_IDX     = 0,
    SBK_Qt3DAnimation_QAnimationCallback_IDX                 = 11,
    SBK_Qt3DAnimation_QAnimationClip_IDX                     = 13,
    SBK_Qt3DAnimation_QAnimationClipData_IDX                 = 14,
    SBK_Qt3DAnimation_QAnimationClipLoader_Status_IDX        = 16,
    SBK_Qt3DAnimation_QAnimationClipLoader_IDX               = 15,
    SBK_Qt3DAnimation_QAnimationController_IDX               = 17,
    SBK_Qt3DAnimation_QAnimationGroup_IDX                    = 18,
    SBK_Qt3DAnimation_QBlendedClipAnimator_IDX               = 19,
    SBK_Qt3DAnimation_QCallbackMapping_IDX                   = 20,
    SBK_Qt3DAnimation_QChannel_IDX                           = 21,
    SBK_Qt3DAnimation_QChannelComponent_IDX                  = 22,
    SBK_Qt3DAnimation_QChannelMapper_IDX                     = 23,
    SBK_Qt3DAnimation_QChannelMapping_IDX                    = 24,
    SBK_Qt3DAnimation_QClipAnimator_IDX                      = 25,
    SBK_Qt3DAnimation_QClipBlendValue_IDX                    = 26,
    SBK_Qt3DAnimation_QClock_IDX                             = 27,
    SBK_Qt3DAnimation_QKeyFrame_InterpolationType_IDX        = 29,
    SBK_Qt3DAnimation_QKeyFrame_IDX                          = 28,
    SBK_Qt3DAnimation_QKeyframeAnimation_RepeatMode_IDX      = 31,
    SBK_Qt3DAnimation_QKeyframeAnimation_IDX                 = 30,
    SBK_Qt3DAnimation_QLerpClipBlend_IDX                     = 32,
    SBK_Qt3DAnimation_QMorphTarget_IDX                       = 33,
    SBK_Qt3DAnimation_QMorphingAnimation_Method_IDX          = 35,
    SBK_Qt3DAnimation_QMorphingAnimation_IDX                 = 34,
    SBK_Qt3DAnimation_QSkeletonMapping_IDX                   = 36,
    SBK_Qt3DAnimation_QVertexBlendAnimation_IDX              = 37,
    SBK_Qt3DAnimation_IDX_COUNT                              = 38,
};

// This variable stores all Python types exported by this module.
extern Shiboken::Module::TypeInitStruct *SbkPySide6_Qt3DAnimationTypeStructs;

// This variable stores the Python module object exported by this module.
extern PyObject *SbkPySide6_Qt3DAnimationModuleObject;

// This variable stores all type converters exported by this module.
extern SbkConverter **SbkPySide6_Qt3DAnimationTypeConverters;

// Converter indices
enum [[deprecated]] : int {
    SBK_QT3DANIMATION_QLIST_INT_IDX                          = 0, // QList<int>
    SBK_QT3DANIMATION_QLIST_FLOAT_IDX                        = 1, // QList<float>
    SBK_QT3DANIMATION_QLIST_QT3DCORE_QTRANSFORMPTR_IDX       = 2, // QList<Qt3DCore::QTransform*>
    SBK_QT3DANIMATION_QLIST_QT3DANIMATION_QMORPHTARGETPTR_IDX = 3, // QList<Qt3DAnimation::QMorphTarget*>
    SBK_QT3DANIMATION_QLIST_QT3DANIMATION_QABSTRACTCHANNELMAPPINGPTR_IDX = 4, // QList<Qt3DAnimation::QAbstractChannelMapping*>
    SBK_QT3DANIMATION_STD_VECTOR_QSHAREDPOINTER_QT3DCORE_QASPECTJOB_IDX = 5, // std::vector<QSharedPointer<Qt3DCore::QAspectJob>>
    SBK_QT3DANIMATION_QLIST_QT3DANIMATION_QABSTRACTANIMATIONPTR_IDX = 6, // QList<Qt3DAnimation::QAbstractAnimation*>
    SBK_QT3DANIMATION_QLIST_QT3DANIMATION_QANIMATIONGROUPPTR_IDX = 7, // QList<Qt3DAnimation::QAnimationGroup*>
    SBK_QT3DANIMATION_QLIST_QT3DCORE_QATTRIBUTEPTR_IDX       = 8, // QList<Qt3DCore::QAttribute*>
    SBK_QT3DANIMATION_QLIST_QVARIANT_IDX                     = 9, // QList<QVariant>
    SBK_QT3DANIMATION_QLIST_QSTRING_IDX                      = 10, // QList<QString>
    SBK_QT3DANIMATION_QMAP_QSTRING_QVARIANT_IDX              = 11, // QMap<QString,QVariant>
    SBK_QT3DANIMATION_CONVERTERS_IDX_COUNT                   = 12,
};

// Converter indices
enum : int {
    SBK_Qt3DAnimation_QList_int_IDX                          = 0, // QList<int>
    SBK_Qt3DAnimation_QList_float_IDX                        = 1, // QList<float>
    SBK_Qt3DAnimation_QList_Qt3DCore_QTransformPTR_IDX       = 2, // QList<Qt3DCore::QTransform*>
    SBK_Qt3DAnimation_QList_Qt3DAnimation_QMorphTargetPTR_IDX = 3, // QList<Qt3DAnimation::QMorphTarget*>
    SBK_Qt3DAnimation_QList_Qt3DAnimation_QAbstractChannelMappingPTR_IDX = 4, // QList<Qt3DAnimation::QAbstractChannelMapping*>
    SBK_Qt3DAnimation_std_vector_QSharedPointer_Qt3DCore_QAspectJob_IDX = 5, // std::vector<QSharedPointer<Qt3DCore::QAspectJob>>
    SBK_Qt3DAnimation_QList_Qt3DAnimation_QAbstractAnimationPTR_IDX = 6, // QList<Qt3DAnimation::QAbstractAnimation*>
    SBK_Qt3DAnimation_QList_Qt3DAnimation_QAnimationGroupPTR_IDX = 7, // QList<Qt3DAnimation::QAnimationGroup*>
    SBK_Qt3DAnimation_QList_Qt3DCore_QAttributePTR_IDX       = 8, // QList<Qt3DCore::QAttribute*>
    SBK_Qt3DAnimation_QList_QVariant_IDX                     = 9, // QList<QVariant>
    SBK_Qt3DAnimation_QList_QString_IDX                      = 10, // QList<QString>
    SBK_Qt3DAnimation_QMap_QString_QVariant_IDX              = 11, // QMap<QString,QVariant>
    SBK_Qt3DAnimation_CONVERTERS_IDX_COUNT                   = 12,
};
// Macros for type check

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
namespace Shiboken
{

// PyType functions, to get the PyObjectType for a type T
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAbstractAnimation::AnimationType >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAbstractAnimation_AnimationType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAbstractAnimation >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAbstractAnimation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAbstractAnimationClip >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAbstractAnimationClip_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAbstractChannelMapping >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAbstractChannelMapping_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAbstractClipAnimator::Loops >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAbstractClipAnimator_Loops_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAbstractClipAnimator >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAbstractClipAnimator_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAbstractClipBlendNode >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAbstractClipBlendNode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAdditiveClipBlend >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAdditiveClipBlend_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationAspect >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationAspect_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationCallback::Flag >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationCallback_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::QFlags<Qt3DAnimation::QAnimationCallback::Flag> >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_QFlags_Qt3DAnimation_QAnimationCallback_Flag_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationCallback >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationCallback_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationClip >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationClip_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationClipData >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationClipData_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationClipLoader::Status >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationClipLoader_Status_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationClipLoader >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationClipLoader_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationController >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationController_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QAnimationGroup >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QAnimationGroup_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QBlendedClipAnimator >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QBlendedClipAnimator_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QCallbackMapping >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QCallbackMapping_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QChannel >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QChannel_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QChannelComponent >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QChannelComponent_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QChannelMapper >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QChannelMapper_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QChannelMapping >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QChannelMapping_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QClipAnimator >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QClipAnimator_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QClipBlendValue >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QClipBlendValue_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QClock >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QClock_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QKeyFrame::InterpolationType >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QKeyFrame_InterpolationType_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QKeyFrame >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QKeyFrame_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QKeyframeAnimation::RepeatMode >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QKeyframeAnimation_RepeatMode_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QKeyframeAnimation >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QKeyframeAnimation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QLerpClipBlend >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QLerpClipBlend_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QMorphTarget >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QMorphTarget_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QMorphingAnimation::Method >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QMorphingAnimation_Method_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QMorphingAnimation >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QMorphingAnimation_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QSkeletonMapping >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QSkeletonMapping_IDX]); }
template<> inline PyTypeObject *SbkType< ::Qt3DAnimation::QVertexBlendAnimation >() { return Shiboken::Module::get(SbkPySide6_Qt3DAnimationTypeStructs[SBK_Qt3DAnimation_QVertexBlendAnimation_IDX]); }

} // namespace Shiboken

QT_WARNING_POP
#endif // SBK_QT3DANIMATION_PYTHON_H

