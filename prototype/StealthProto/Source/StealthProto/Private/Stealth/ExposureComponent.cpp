#include "Stealth/ExposureComponent.h"

#include "Stealth/StealthLightingSubsystem.h"

#include "DrawDebugHelpers.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

UExposureComponent::UExposureComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickInterval = UpdateInterval;
}

void UExposureComponent::BeginPlay()
{
	Super::BeginPlay();

	PrimaryComponentTick.TickInterval = UpdateInterval;

	// 스폰 직후 한 프레임 동안 값이 0으로 보이지 않도록 즉시 한 번 계산하고,
	// 보간 없이 초기값을 확정한다.
	UpdateExposure();
	CurrentExposure = TargetExposure;
	CurrentState = EvaluateState(CurrentExposure);
}

void UExposureComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	UpdateExposure();

	CurrentExposure = FMath::FInterpTo(CurrentExposure, TargetExposure, DeltaTime, InterpSpeed);

	const EExposureState NewState = EvaluateState(CurrentExposure);
	if (NewState != CurrentState)
	{
		const EExposureState OldState = CurrentState;
		CurrentState = NewState;
		OnExposureStateChanged.Broadcast(NewState, OldState);
	}
}

void UExposureComponent::UpdateExposure()
{
	const AActor* Owner = GetOwner();
	const UWorld* World = GetWorld();
	if (!Owner || !World || SampleOffsets.Num() == 0)
	{
		TargetExposure = 0.f;
		return;
	}

	UStealthLightingSubsystem* Lighting = World->GetSubsystem<UStealthLightingSubsystem>();
	if (!Lighting)
	{
		TargetExposure = 0.f;
		return;
	}

	const FVector Origin = Owner->GetActorLocation();
	float Sum = 0.f;

	for (const FVector& Offset : SampleOffsets)
	{
		// 오프셋은 액터 회전과 무관하게 월드 기준으로 둔다. 캐릭터가 돌아도
		// 머리 높이는 그대로여야 하기 때문이다.
		const FVector SampleLocation = Origin + Offset;

		const float Brightness = Lighting->ComputeBrightnessAtLocation(SampleLocation, Owner, bDrawDebug ? UpdateInterval : 0.f);
		const float Normalized = FMath::Clamp(Brightness / FMath::Max(ReferenceBrightness, 1.f), 0.f, 1.f);
		Sum += Normalized;

		if (bDrawDebug)
		{
			const FColor Color = FColor::MakeRedToGreenColorFromScalar(1.f - Normalized);
			DrawDebugSphere(World, SampleLocation, 8.f, 8, Color, false, UpdateInterval, 0, 0.5f);
		}
	}

	TargetExposure = Sum / SampleOffsets.Num();

	if (bDrawDebug)
	{
		const FString Text = FString::Printf(TEXT("Exposure %.2f (%s) / Lights %d"),
			CurrentExposure,
			*UEnum::GetDisplayValueAsText(CurrentState).ToString(),
			Lighting->GetRegisteredLightCount());

		DrawDebugString(World, Origin + FVector(0.f, 0.f, 200.f), Text, nullptr, FColor::White, UpdateInterval, true);
	}
}

EExposureState UExposureComponent::EvaluateState(float Exposure) const
{
	// 현재 단계에서 벗어날 때만 히스테리시스만큼 더 요구한다. 그림자 경계에서
	// 단계가 매 프레임 뒤집히는 것을 막는다.
	switch (CurrentState)
	{
	case EExposureState::Hidden:
		return Exposure > HiddenThreshold + StateHysteresis
			? (Exposure >= LitThreshold + StateHysteresis ? EExposureState::Lit : EExposureState::Dim)
			: EExposureState::Hidden;

	case EExposureState::Lit:
		return Exposure < LitThreshold - StateHysteresis
			? (Exposure <= HiddenThreshold - StateHysteresis ? EExposureState::Hidden : EExposureState::Dim)
			: EExposureState::Lit;

	case EExposureState::Dim:
	default:
		if (Exposure >= LitThreshold + StateHysteresis)
		{
			return EExposureState::Lit;
		}
		if (Exposure <= HiddenThreshold - StateHysteresis)
		{
			return EExposureState::Hidden;
		}
		return EExposureState::Dim;
	}
}
