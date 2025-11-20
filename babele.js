// CoC7-KR - Babele registration for Call of Cthulhu 7th

Hooks.once("init", () => {
  // Babele 모듈이 켜져 있는지 확인
  const babeleModule = game.modules.get("babele");
  if (!babeleModule || !babeleModule.active) {
    console.warn("CoC7-KR | Babele module is not active. Translation will not be applied.");
    return;
  }

  // Babele에 이 모듈의 번역을 등록
  game.babele.register({
    module: "CoC7th-KR",   // module.json 의 id와 동일해야 함
    lang: "ko",
    dir: "compendium"    // 모듈 루트 기준 번역용 폴더
  });

  console.log("CoC7-KR | Babele translation module initialized.");
});
