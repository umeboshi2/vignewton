<div class="main-betgames-view">
  <div class="view-header">
    <p>NFL Bettable Games</p>
  </div>
  <div class="view-list">
    NFL Teams
    %for odds in olist:
    <div class="view-list-entry">
      <% favored = '%s %s' % (odds.favored.city, odds.favored.name) %>
      <% underdog = '%s %s' % (odds.underdog.city, odds.underdog.name) %>
      <% summary = odds.game.summary %>
      ${summary}<br>
      ${favored} over ${underdog} by ${odds.spread} totalling ${odds.total}<br>
    </div>
    %endfor
  </div>
</div>
