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
      var pct=cur*100;
      track.style.transform='translateX(-'+pct+'%)';
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
</script>