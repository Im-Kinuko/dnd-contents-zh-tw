const MODULE_ID = 'dnd-contents-zh-tw'; // Change this ID!


Hooks.on('init', () => {
  game.settings.register(MODULE_ID, 'autoRegisterBabel', {
    name: '自動實作 Babele 翻譯',
    hint: '自動實作 Babele 翻譯，無需指向包含翻譯的目錄。',
    scope: 'world',
    config: true,
    default: true,
    type: Boolean,
    onChange: value => {
      if (value) {
        autoRegisterBabel();
      }

      window.location.reload();
    },
  });
  game.babele.registerConverters({
    "activities": Converters.activities(),
    "advancement": Converters.advancement(),
    "effects": Converters.effects()
  });


  if (game.settings.get(MODULE_ID, 'autoRegisterBabel')) {
    autoRegisterBabel();
  }
});



/**
 * 支援在地化的子目錄清單（依書籍或官方/第三方模組分類）
 * 
 * 未來當您在此模組中新增其他書籍或模組的翻譯時（例如怪物圖鑑、塔莎萬事屋等），
 * 只需在專案目錄 `compendium/zh-tw/` 下建立對應的子資料夾，並將資料夾名稱加入此陣列即可自動完成註冊。
 */
const MODULE_TRANSLATION_DIRS = [
  'dnd-players-handbook',
  'dnd-dungeon-masters-guide',
  'dnd-adventures-faerun',
  'dnd-heros-faerun',
  'dnd-monster-manual',
  'dnd-ravenloft-horros-within',
  'dnd5e',
  'dnd-forge-artificer',
];

/**
 * 自動執行 Babele 翻譯註冊
 * 透過迴圈自動為各個子目錄完成註冊，同時相容原本根目錄下的翻譯檔案。
 */
function autoRegisterBabel() {
  if (typeof Babele !== 'undefined') {
    // 1. 註冊根目錄（保留對未分類或通用字典等共用翻譯檔的相容與向後相容）
    game.babele.register({
      module: MODULE_ID,
      lang: 'zh-tw',
      dir: 'compendium/zh-tw',
    });

    // 2. 迴圈自動註冊 MODULE_TRANSLATION_DIRS 中所有書籍/模組的子目錄
    MODULE_TRANSLATION_DIRS.forEach(subDir => {
      game.babele.register({
        module: MODULE_ID,
        lang: 'zh-tw',
        dir: `compendium/zh-tw/${subDir}`,
      });
    });
  }
}

export class Converters {
  static activities() {
    return (activities, translations) => Converters._activities(activities, translations);
  }

  static _activities(activities, translations) {
    if (!translations) return activities;

    Object.keys(activities).forEach(key => {
      const activity = activities[key];
      const translationKey = activity.name?.length ? activity.name : activity.type;
      const translation = translations[activity._id] || translations[translationKey];
      if (translation) {
        foundry.utils.mergeObject(activity, {
          name: translation.name ?? activity.name,
          activation: { condition: translation.condition ?? activity.activation?.condition },
          description: { chatFlavor: translation.chatFlavor ?? activity.description?.chatFlavor },
          profiles: activity.profiles ? Converters.summonProfiles(activity.profiles, translation.profiles) : activity.profiles
        });
      }
    });

    return activities;
  }

  static summonProfiles(profiles, translations) {
    if (!translations) return profiles;

    if (Array.isArray(profiles)) {
      return profiles.map(profile => {
        const translation = translations[profile.name];
        if (translation) {
          return foundry.utils.mergeObject(profile, { name: translation.name ?? profile.name });
        }
        return profile;
      });
    }

    return profiles;
  }

  static advancement() {
    return (advancements, translations) => Converters._advancement(advancements, translations);
  }

  static _advancement(advancements, translations) {
    if (!translations || !advancements) return advancements;

    const translateAdv = adv => {
      if (!adv || typeof adv !== 'object') return adv;
      const translation = translations[adv._id] || translations[adv.title];
      if (translation) {
        return foundry.utils.mergeObject(adv, {
          title: translation.title ?? adv.title,
          hint: translation.hint ?? adv.hint,
          configuration: {
            identifier: adv.configuration?.identifier?.length > 0 ? adv.configuration.identifier : adv.title?.slugify()
          }
        });
      }
      return adv;
    };

    if (Array.isArray(advancements)) {
      return advancements.map(adv => translateAdv(adv));
    }

    if (typeof advancements === 'object') {
      if (typeof advancements.map === 'function') {
        return advancements.map(adv => translateAdv(adv));
      }
      Object.keys(advancements).forEach(key => {
        advancements[key] = translateAdv(advancements[key]);
      });
      return advancements;
    }

    return advancements;
  }

  static effects() {
    return (data, translations) => Converters._effects(data, translations);
  }

  static _effects(data, translations) {
    if (!translations || !data || typeof data !== 'object') {
      return data ?? translations;
    }

    const translateEffect = effect => {
      if (!effect || typeof effect !== 'object') return effect;
      const translation = translations[effect._id] || translations[effect.name];
      if (translation) {
        return foundry.utils.mergeObject(effect, {
          name: translation.name ?? effect.name,
          description: translation.description ?? effect.description,
          changes: translation.changes ?? effect.changes
        });
      }
      return effect;
    };

    if (Array.isArray(data)) {
      return data.map(effect => translateEffect(effect));
    }

    if (typeof data.map === 'function') {
      return data.map(effect => translateEffect(effect));
    }

    Object.keys(data).forEach(key => {
      data[key] = translateEffect(data[key]);
    });

    return data;
  }
}


