"""Revert carousel from slide back to fade crossfade."""
import os

FILES = [
    "index.html",
    "motogp-article-martin-topspeed.html",
    "motogp-article-aero-wings.html",
    "motogp-article-aero-wings.himl.html",
    "wsbk-gong-sponsors.html",
]

OLD_CSS = """\
      /* ─── AD CAROUSEL SLIDE ─── */
    .ad-carousel { position:relative; width:100%; aspect-ratio:2164/292; overflow:hidden; display:block; background:#0a0a0a; }
    .ad-track { display:flex; height:100%; transition:transform .65s cubic-bezier(.4,0,.2,1); will-change:transform; }
    .ad-track img { flex:0 0 100%; width:100%; height:100%; object-fit:cover; cursor:pointer; display:block; }"""

NEW_CSS = """\
      /* ─── AD CAROUSEL FADE ─── */
    .ad-carousel { position:relative; width:100%; aspect-ratio:2164/292; overflow:hidden; display:block; background:#0a0a0a; }
    .ad-carousel img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0; transition:opacity .8s ease; cursor:pointer; display:block; }
    .ad-carousel img.ad-active { opacity:1; }"""

OLD_INNER = """\
  <div class="ad-track">
    <img src="images/ad-motul-leaderboard.jpg" alt="Motul 300V — Ride Beyond">
    <img src="images/ad-alpinestars-leaderboard.jpg" alt="Alpinestars Sportswear">
    <img src="images/ad-motul-leaderboard.jpg" alt="Motul 300V" aria-hidden="true">
  </div>
</div>"""

NEW_INNER = """\
  <img src="images/ad-motul-leaderboard.jpg" alt="Motul 300V — Ride Beyond">
  <img src="images/ad-alpinestars-leaderboard.jpg" alt="Alpinestars Sportswear">
</div>"""

OLD_JS = """\
<script>
(function(){
  document.querySelectorAll('.ad-carousel').forEach(function(c){
    var track=c.querySelector('.ad-track');
    if(!track)return;
    var links=JSON.parse(c.dataset.links||'[]');
    var count=links.length, cur=0;
    track.querySelectorAll('img').forEach(function(img,i){
      img.onclick=function(){var li=i>=count?0:i;if(links[li])window.open(links[li],'_blank','noopener');};
    });
    setInterval(function(){
      cur++;
      track.style.transform='translateX(-'+(cur*100)+'%)';
      if(cur>=count){
        setTimeout(function(){
          track.style.transition='none';
          track.style.transform='translateX(0)';
          cur=0;
          requestAnimationFrame(function(){requestAnimationFrame(function(){
            track.style.transition='transform .65s cubic-bezier(.4,0,.2,1)';
          });});
        },700);
      }
    },5000);
  });
})();
</script>"""

NEW_JS = """\
<script>
(function(){
  document.querySelectorAll('.ad-carousel').forEach(function(c){
    var imgs=c.querySelectorAll('img');
    var links=JSON.parse(c.dataset.links||'[]');
    var cur=0;
    if(imgs[0]) imgs[0].classList.add('ad-active');
    imgs.forEach(function(img,i){
      img.onclick=function(){if(links[i])window.open(links[i],'_blank','noopener');};
    });
    if(imgs.length>1){
      setInterval(function(){
        imgs[cur].classList.remove('ad-active');
        cur=(cur+1)%imgs.length;
        imgs[cur].classList.add('ad-active');
      },5000);
    }
  });
})();
</script>"""

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for fname in FILES:
    fpath = os.path.join(BASE, fname)
    if not os.path.exists(fpath):
        print(f"SKIP: {fname}")
        continue
    with open(fpath, encoding="utf-8") as f:
        content = f.read()
    changed = False
    for old, new in [(OLD_CSS, NEW_CSS), (OLD_INNER, NEW_INNER), (OLD_JS, NEW_JS)]:
        if old in content:
            content = content.replace(old, new)
            changed = True
    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {fname}")
    else:
        print(f"No change: {fname}")
print("Done.")
