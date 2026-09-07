#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ExposureComponent.generated.h"

/** 라이트 미터의 단계. 게임플레이 판정은 이 단계로 하고, 연속값은 UI에만 쓴다. */
UENUM(BlueprintType)
enum class EExposureState : uint8
{
	/** 완전한 어둠. 사실상 보이지 않는다. */
	Hidden,
	/** 어스름. 가만히 있으면 잘 안 보이지만 움직이면 눈에 띈다. */
	Dim,
	/** 밝은 곳. 시야에 들어오면 바로 발각된다. */
	Lit
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnExposureStateChanged, EExposureState, NewState, EExposureState, OldState);

/**
 * 소유 액터가 현재 얼마나 빛에 노출되어 있는지 계산한다.
 *
 * 한 점이 아니라 여러 지점(기본: 머리/몸통/발)을 재서 평균을 낸다. 한 점만
 * 재면 "상체만 빛에 걸린" 상황을 표현할 수 없어 판정이 딱딱해진다.
 */
UCLASS(ClassGroup = (Stealth), meta = (BlueprintSpawnableComponent))
class STEALTHPROTO_API UExposureComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UExposureComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** 0~1로 정규화된 현재 노출값. UI(라이트 미터)에 그대로 쓸 수 있다. */
	UFUNCTION(BlueprintPure, Category = "Stealth")
	float GetExposure() const { return CurrentExposure; }

	/** 보간되지 않은 즉시 노출값. 게임플레이 판정에 지연이 곤란할 때. */
	UFUNCTION(BlueprintPure, Category = "Stealth")
	float GetRawExposure() const { return TargetExposure; }

	UFUNCTION(BlueprintPure, Category = "Stealth")
	EExposureState GetExposureState() const { return CurrentState; }

	/** 노출 단계가 바뀔 때. AI 감지나 UI 연출을 여기에 연결한다. */
	UPROPERTY(BlueprintAssignable, Category = "Stealth")
	FOnExposureStateChanged OnExposureStateChanged;

protected:
	/**
	 * 소유 액터 기준 상대 측정 지점. 기본값은 사람 크기 캐릭터의
	 * 머리(z=160) / 몸통(z=90) / 발(z=20)이다.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth")
	TArray<FVector> SampleOffsets = {
		FVector(0.f, 0.f, 160.f),
		FVector(0.f, 0.f, 90.f),
		FVector(0.f, 0.f, 20.f)
	};

	/**
	 * 이 밝기를 노출 1.0으로 본다. 레벨의 조명 세기에 맞춰 조정하는
	 * 프로젝트 전체의 기준값이다. 튜닝은 대부분 이 값 하나로 끝난다.
	 *
	 * 기본값은 UE5 포인트라이트의 기본 광량(칸델라) 기준이다. 광원 세기를
	 * 크게 바꿨다면 디버그 표시를 켜고 밝은 곳에서 1.0에 닿도록 맞출 것.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.01"))
	float ReferenceBrightness = 8.f;

	/** 노출값 갱신 주기(초). 매 프레임 계산할 필요가 없다. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0"))
	float UpdateInterval = 0.1f;

	/** 표시값 보간 속도. 미터가 튀지 않게 한다. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0"))
	float InterpSpeed = 6.f;

	/** 이 값 이하면 Hidden. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float HiddenThreshold = 0.15f;

	/** 이 값 이상이면 Lit. 사이는 Dim. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float LitThreshold = 0.45f;

	/**
	 * 단계 전이에 적용할 히스테리시스. 임계값 근처에서 단계가 떨리는 것을 막는다.
	 * 그림자 경계에 서 있을 때 AI가 발작하듯 반응하는 것을 방지한다.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth", meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float StateHysteresis = 0.05f;

	/** 측정 지점과 기여 광원을 화면에 그린다. 튜닝할 때 반드시 켤 것. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stealth|Debug")
	bool bDrawDebug = false;

private:
	void UpdateExposure();
	EExposureState EvaluateState(float Exposure) const;

	float CurrentExposure = 0.f;
	float TargetExposure = 0.f;
	EExposureState CurrentState = EExposureState::Hidden;
};
