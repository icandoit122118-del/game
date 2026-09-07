using UnrealBuildTool;

public class StealthProtoTarget : TargetRules
{
	public StealthProtoTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("StealthProto");
	}
}
