#include "PCH.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace logger = SKSE::log;

namespace
{
	constexpr int kMaxLegs = 8;

	struct Settings
	{
		bool  enabled{ true };
		bool  forceFootIK{ true };
		bool  extraRaycasts{ true };
		bool  skipMannequins{ true };
		bool  skipFirstPerson{ true };
		bool  playerOnly{ false };
		float raycastHeight{ 36.0f };
		float raycastLength{ 72.0f };
		float minGroundNormalZ{ 0.45f };
		float maxFootOffset{ 24.0f };
		float extraSmooth{ 0.08f };
	};

	struct ExtraOffset
	{
		bool  set{ false };
		float x{ 0.0f };
		float y{ 0.0f };
		float z{ 0.0f };
	};

	struct ProjectCfg
	{
		ExtraOffset legs[kMaxLegs]{};
		int         count{ 0 };
	};

	struct ActorIKState
	{
		float extraZ[kMaxLegs]{};
	};

	Settings g_settings;
	std::unordered_map<std::string, ProjectCfg> g_projects;
	std::mutex g_stateMutex;
	std::unordered_map<std::uint32_t, ActorIKState> g_state;

	std::string Lower(std::string s)
	{
		for (char& c : s) {
			c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
		}
		return s;
	}

	bool ContainsI(const char* hay, const char* needle)
	{
		if (!hay || !needle || !*needle) {
			return false;
		}
		const std::string h = Lower(hay);
		const std::string n = Lower(needle);
		return h.find(n) != std::string::npos;
	}

	std::filesystem::path PluginDir()
	{
		wchar_t buf[MAX_PATH]{};
		HMODULE mod = nullptr;
		GetModuleHandleExW(
			GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
			reinterpret_cast<LPCWSTR>(&PluginDir),
			&mod);
		GetModuleFileNameW(mod, buf, MAX_PATH);
		return std::filesystem::path(buf).parent_path();
	}

	std::filesystem::path GameDataDir()
	{
		wchar_t buf[MAX_PATH]{};
		GetModuleFileNameW(GetModuleHandleW(nullptr), buf, MAX_PATH);
		return std::filesystem::path(buf).parent_path() / L"Data";
	}

	float Clampf(float v, float lo, float hi)
	{
		return std::max(lo, std::min(hi, v));
	}

	float Lerp(float a, float b, float t)
	{
		return a + (b - a) * Clampf(t, 0.0f, 1.0f);
	}

	bool ReadBoolLine(const std::string& line, const char* key, bool& out)
	{
		const std::string prefix = std::string(key) + "=";
		if (line.rfind(prefix, 0) != 0) {
			return false;
		}
		const auto v = line.substr(prefix.size());
		out = (v == "1" || v == "true" || v == "True");
		return true;
	}

	bool ReadFloatLine(const std::string& line, const char* key, float& out)
	{
		const std::string prefix = std::string(key) + "=";
		if (line.rfind(prefix, 0) != 0) {
			return false;
		}
		out = std::strtof(line.c_str() + prefix.size(), nullptr);
		return true;
	}

	void LoadPluginIni()
	{
		const auto path = PluginDir() / L"FootIKFix.ini";
		std::ifstream in(path);
		if (!in) {
			logger::warn("FootIKFix.ini missing at {}, using defaults", path.string());
			return;
		}
		std::string line;
		while (std::getline(in, line)) {
			if (!line.empty() && line.back() == '\r') {
				line.pop_back();
			}
			ReadBoolLine(line, "bEnabled", g_settings.enabled);
			ReadBoolLine(line, "bForceFootIK", g_settings.forceFootIK);
			ReadBoolLine(line, "bExtraRaycasts", g_settings.extraRaycasts);
			ReadBoolLine(line, "bSkipMannequins", g_settings.skipMannequins);
			ReadBoolLine(line, "bSkipFirstPerson", g_settings.skipFirstPerson);
			ReadBoolLine(line, "bPlayerOnly", g_settings.playerOnly);
			ReadFloatLine(line, "fRaycastHeight", g_settings.raycastHeight);
			ReadFloatLine(line, "fRaycastLength", g_settings.raycastLength);
			ReadFloatLine(line, "fMinGroundNormalZ", g_settings.minGroundNormalZ);
			ReadFloatLine(line, "fMaxFootOffset", g_settings.maxFootOffset);
			ReadFloatLine(line, "fExtraSmooth", g_settings.extraSmooth);
		}
	}

	void LoadProjectIni(const std::filesystem::path& path)
	{
		std::ifstream in(path);
		if (!in) {
			return;
		}
		ProjectCfg cfg;
		std::string line;
		while (std::getline(in, line)) {
			if (!line.empty() && line.back() == '\r') {
				line.pop_back();
			}
			if (line.empty() || line.front() == ';' || line.front() == '#' || line.front() == '[') {
				continue;
			}
			const auto eq = line.find('=');
			if (eq == std::string::npos) {
				continue;
			}
			auto key = line.substr(0, eq);
			auto val = line.substr(eq + 1);
			while (!key.empty() && (key.back() == ' ' || key.back() == '\t')) {
				key.pop_back();
			}
			while (!val.empty() && (val.front() == ' ' || val.front() == '\t')) {
				val.erase(val.begin());
			}
			if (key.rfind("leg", 0) != 0 || key.size() < 4) {
				continue;
			}
			const int idx = std::atoi(key.c_str() + 3);
			if (idx < 0 || idx >= kMaxLegs) {
				continue;
			}
			float x = 0.0f;
			float y = 0.0f;
			float z = 0.0f;
			if (std::sscanf(val.c_str(), "%f,%f,%f", &x, &y, &z) != 3) {
				continue;
			}
			cfg.legs[idx] = ExtraOffset{ true, x, y, z };
			cfg.count = std::max(cfg.count, idx + 1);
		}
		const auto stem = Lower(path.stem().string());
		g_projects[stem] = cfg;
	}

	void LoadAllProjectInis()
	{
		g_projects.clear();
		const auto dir = GameDataDir() / L"FootIK";
		std::error_code ec;
		if (!std::filesystem::is_directory(dir, ec)) {
			logger::warn("Data/FootIK missing at {}", dir.string());
			return;
		}
		for (const auto& ent : std::filesystem::directory_iterator(dir, ec)) {
			if (ent.is_regular_file() && Lower(ent.path().extension().string()) == ".ini") {
				LoadProjectIni(ent.path());
			}
		}
		logger::info("FootIKFix loaded {} project ini(s) from {}", g_projects.size(), dir.string());
	}

	const ProjectCfg* FindProject(const char* projectName, RE::Actor* actor)
	{
		if (projectName && *projectName) {
			const auto key = Lower(projectName);
			if (auto it = g_projects.find(key); it != g_projects.end()) {
				return &it->second;
			}
			if (auto it = g_projects.find(key + "project"); it != g_projects.end()) {
				return &it->second;
			}
		}
		const auto* base = actor ? actor->GetActorBase() : nullptr;
		if (base && base->GetSex() == RE::SEX::kFemale) {
			if (auto it = g_projects.find("defaultfemale"); it != g_projects.end()) {
				return &it->second;
			}
		}
		if (auto it = g_projects.find("defaultmale"); it != g_projects.end()) {
			return &it->second;
		}
		return nullptr;
	}

	bool IsMannequin(RE::Actor* actor)
	{
		if (!actor) {
			return false;
		}
		if (const auto* base = actor->GetActorBase(); base && ContainsI(base->GetFormEditorID(), "Mannequin")) {
			return true;
		}
		if (const auto* race = actor->GetRace(); race && ContainsI(race->GetFormEditorID(), "Mannequin")) {
			return true;
		}
		return ContainsI(actor->GetFormEditorID(), "Mannequin");
	}

	bool ShouldSkip(RE::Actor* actor)
	{
		if (!actor || !actor->Is3DLoaded() || actor->IsDead()) {
			return true;
		}
		if (actor->IsInKillMove() || actor->IsInRagdollState() || actor->IsOnMount() || actor->IsSwimming()) {
			return true;
		}
		if (const auto* state = actor->AsActorState()) {
			if (state->GetSitSleepState() != RE::SIT_SLEEP_STATE::kNormal) {
				return true;
			}
			if (state->GetKnockState() != RE::KNOCK_STATE_ENUM::kNormal) {
				return true;
			}
		}
		if (g_settings.skipMannequins && IsMannequin(actor)) {
			return true;
		}
		if (g_settings.playerOnly && !actor->IsPlayerRef()) {
			return true;
		}
		return false;
	}

	RE::BShkbAnimationGraph* ActiveGraph(RE::Actor* actor)
	{
		RE::BSTSmartPointer<RE::BSAnimationGraphManager> mgr;
		if (!actor->GetAnimationGraphManager(mgr) || !mgr) {
			return nullptr;
		}
		auto& graphs = mgr->graphs;
		if (graphs.empty()) {
			return nullptr;
		}
		std::uint32_t idx = mgr->GetRuntimeData().activeGraph;
		if (idx >= graphs.size()) {
			idx = 0;
		}
		return graphs[static_cast<std::uint32_t>(idx)].get();
	}

	void ForceFootIK(RE::Actor* actor, RE::BShkbAnimationGraph* graph)
	{
		if (!g_settings.forceFootIK || !graph) {
			return;
		}
		graph->doFootIK = 1;
		if (auto* driver = graph->characterInstance.footIkDriver.get()) {
			driver->disableFootIk = 0;
		}
		static const RE::BSFixedString kWants{ "bGraphWantsFootIK" };
		static const RE::BSFixedString kDisable{ "bHumanoidFootIKDisable" };
		static const RE::BSFixedString kOnOff{ "fIKOnOffGain" };
		actor->SetGraphVariableBool(kWants, true);
		actor->SetGraphVariableBool(kDisable, false);
		actor->SetGraphVariableFloat(kOnOff, 1.0f);
	}

	bool RaycastGround(
		RE::Actor* actor,
		const RE::NiPoint3& origin,
		const RE::NiPoint3& dest,
		RE::NiPoint3& hitPoint,
		RE::NiPoint3& hitNormal)
	{
		auto* cell = actor->GetParentCell();
		if (!cell) {
			return false;
		}
		auto* world = cell->GetbhkWorld();
		if (!world) {
			return false;
		}
		const float scale = RE::bhkWorld::GetWorldScale();
		RE::bhkPickData pick;
		pick.rayInput.from = RE::hkVector4(origin * scale);
		pick.rayInput.to = RE::hkVector4(dest * scale);
		actor->GetCollisionFilterInfo(pick.rayInput.filterInfo);
		world->PickObject(pick);
		if (!pick.rayOutput.HasHit()) {
			return false;
		}
		hitPoint = origin + (dest - origin) * pick.rayOutput.hitFraction;
		hitNormal = RE::NiPoint3(
			pick.rayOutput.normal.quad.m128_f32[0],
			pick.rayOutput.normal.quad.m128_f32[1],
			pick.rayOutput.normal.quad.m128_f32[2]);
		if (hitNormal.Length() > 1e-4f) {
			hitNormal.Unitize();
		} else {
			hitNormal = RE::NiPoint3(0.0f, 0.0f, 1.0f);
		}
		return hitNormal.z >= g_settings.minGroundNormalZ;
	}

	void SetWorldTranslate(RE::NiAVObject* node, const RE::NiPoint3& world)
	{
		if (!node) {
			return;
		}
		if (auto* parent = node->parent) {
			node->local.translate = parent->world.rotate.Transpose() * (world - parent->world.translate);
		} else {
			node->local.translate = world;
		}
	}

	RE::NiAVObject* FindNode(RE::NiAVObject* root, const char* name)
	{
		return root ? root->GetObjectByName(name) : nullptr;
	}

	void BindFeet(RE::NiAVObject* root, RE::NiAVObject** feet, int maxFeet)
	{
		static const char* kNames[] = {
			"NPC L Foot [Lft ]",
			"NPC R Foot [Rft ]",
			"NPC L HorseFoot [LHft]",
			"NPC R HorseFoot [RHft]",
			"NPC L Toe0 [LToe]",
			"NPC R Toe0 [RToe]",
		};
		int n = 0;
		for (const char* name : kNames) {
			if (n >= maxFeet) {
				break;
			}
			if (auto* node = FindNode(root, name)) {
				feet[n++] = node;
			}
		}
	}

	void ApplyExtraRaycasts(RE::Actor* actor, RE::BShkbAnimationGraph* graph, float dt)
	{
		if (!g_settings.extraRaycasts || !graph) {
			return;
		}
		if (g_settings.skipFirstPerson && actor->IsPlayerRef()) {
			if (auto* cam = RE::PlayerCamera::GetSingleton(); cam && cam->IsInFirstPerson()) {
				return;
			}
		}
		bool jumping = false;
		actor->GetGraphVariableBool("bInJumpState", jumping);
		if (jumping) {
			return;
		}
		const auto* proj = FindProject(graph->projectName.c_str(), actor);
		if (!proj || proj->count <= 0) {
			return;
		}
		auto* root = actor->Get3D(false);
		if (!root) {
			return;
		}
		RE::NiAVObject* feet[kMaxLegs]{};
		BindFeet(root, feet, kMaxLegs);

		ActorIKState local;
		{
			std::lock_guard lock(g_stateMutex);
			local = g_state[actor->GetFormID()];
		}
		const float smooth = (g_settings.extraSmooth > 0.0f) ? Clampf(dt / g_settings.extraSmooth, 0.0f, 1.0f) : 1.0f;
		const float h = g_settings.raycastHeight;
		const float len = g_settings.raycastLength;
		bool any = false;

		for (int i = 0; i < proj->count && i < kMaxLegs; ++i) {
			const auto& off = proj->legs[i];
			if (!off.set) {
				continue;
			}
			if (std::abs(off.x) < 1e-4f && std::abs(off.y) < 1e-4f && std::abs(off.z) < 1e-4f) {
				local.extraZ[i] = Lerp(local.extraZ[i], 0.0f, smooth);
				continue;
			}
			auto* foot = feet[i];
			if (!foot) {
				continue;
			}
			const RE::NiPoint3 localOff(off.x, off.y, off.z);
			const RE::NiPoint3 extra = foot->world.translate + (foot->world.rotate * localOff);
			const RE::NiPoint3 from(extra.x, extra.y, extra.z + h);
			const RE::NiPoint3 to(extra.x, extra.y, from.z - len);
			RE::NiPoint3 hit{};
			RE::NiPoint3 normal{};
			if (!RaycastGround(actor, from, to, hit, normal)) {
				local.extraZ[i] = Lerp(local.extraZ[i], 0.0f, smooth);
				continue;
			}
			float desired = hit.z - extra.z;
			desired = Clampf(desired, -g_settings.maxFootOffset, g_settings.maxFootOffset);
			if (desired < 0.0f) {
				desired = 0.0f;
			}
			local.extraZ[i] = Lerp(local.extraZ[i], desired, smooth);
			if (std::abs(local.extraZ[i]) < 0.01f) {
				continue;
			}
			RE::NiPoint3 planted = foot->world.translate;
			planted.z += local.extraZ[i];
			SetWorldTranslate(foot, planted);
			any = true;
		}

		if (any) {
			RE::NiUpdateData upd{};
			upd.time = dt;
			upd.flags.set(RE::NiUpdateData::Flag::kDirty);
			if (auto* pelvis = FindNode(root, "NPC Pelvis [Pelv]")) {
				pelvis->UpdateDownwardPass(upd, 0);
			} else if (feet[0] && feet[0]->parent) {
				feet[0]->parent->UpdateDownwardPass(upd, 0);
			}
		}

		{
			std::lock_guard lock(g_stateMutex);
			g_state[actor->GetFormID()] = local;
		}
	}

	void ApplyActor(RE::Actor* actor, float dt)
	{
		if (!g_settings.enabled || !actor || ShouldSkip(actor)) {
			return;
		}
		auto* graph = ActiveGraph(actor);
		ForceFootIK(actor, graph);
		ApplyExtraRaycasts(actor, graph, dt);
	}

	void PreUpdate(RE::Actor* actor)
	{
		if (!g_settings.enabled || !actor || ShouldSkip(actor)) {
			return;
		}
		ForceFootIK(actor, ActiveGraph(actor));
	}

	struct PlayerUpdateAnim
	{
		static void thunk(RE::Actor* a_this, float a_delta)
		{
			PreUpdate(a_this);
			func(a_this, a_delta);
			ApplyActor(a_this, a_delta);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	struct CharacterUpdateAnim
	{
		static void thunk(RE::Actor* a_this, float a_delta)
		{
			PreUpdate(a_this);
			func(a_this, a_delta);
			ApplyActor(a_this, a_delta);
		}
		static inline REL::Relocation<decltype(thunk)> func;
	};

	void InstallHooks()
	{
		REL::Relocation<std::uintptr_t> playerVtbl{ RE::PlayerCharacter::VTABLE[0] };
		PlayerUpdateAnim::func = playerVtbl.write_vfunc(0x7D, PlayerUpdateAnim::thunk);
		REL::Relocation<std::uintptr_t> charVtbl{ RE::Character::VTABLE[0] };
		CharacterUpdateAnim::func = charVtbl.write_vfunc(0x7D, CharacterUpdateAnim::thunk);
		logger::info("FootIKFix hooked Actor::UpdateAnimation");
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::Init(a_skse);
	LoadPluginIni();
	LoadAllProjectInis();
	SKSE::GetMessagingInterface()->RegisterListener([](SKSE::MessagingInterface::Message* msg) {
		if (msg->type == SKSE::MessagingInterface::kPostLoad) {
			InstallHooks();
		}
		if (msg->type == SKSE::MessagingInterface::kDataLoaded) {
			LoadAllProjectInis();
		}
		if (msg->type == SKSE::MessagingInterface::kNewGame || msg->type == SKSE::MessagingInterface::kPreLoadGame) {
			std::lock_guard lock(g_stateMutex);
			g_state.clear();
		}
	});
	logger::info("FootIKFix 0.5.0 loaded (SE 1.7.104 Address Library format 5)");
	return true;
}
