<div class="widget-bet-line">
  <% now = datetime.now() %>
  <div class="listview-list-entry">
    <% mkurl = request.route_url %>
    <% game_id = odds.game.id %>
    <% game = odds.game %>
    <% game_url = mkurl('vig_nflgames', context='viewgame', id=game_id) %>
    <% favored_txt = '%s %s' % (odds.favored.city, odds.favored.name) %>
    <% underdog_txt = '%s %s' % (odds.underdog.city, odds.underdog.name) %>
    <% away_txt = '%s %s' % (game.away.city, game.away.name) %>
    <% home_txt = '%s %s' % (game.home.city, game.home.name) %>
    <% summary = odds.game.summary %>
    <% broute = 'vig_betgames' %>
    <% favored_id = 'line-{}-favored'.format(game_id) %>
    <% favored_url = mkurl(broute, context='betfavored', id=game_id) %>
    <% underdog_id = 'line-{}-underdog'.format(game_id) %>
    <% underdog_url = mkurl(broute, context='betunderdog', id=game_id) %>
    <% under_id = 'underover-{}-under'.format(game_id) %>
    <% under_url = mkurl(broute, context='betunder', id=game_id) %>
    <% over_id = 'underover-{}-over'.format(game_id) %>
    <% over_url = mkurl(broute, context='betover', id=game_id) %>
    <% form_url = mkurl('vig_betfrag', context='betover', id='foo') %>
    <a href="${game_url}">${summary}</a><br>
    <div class="line-table">
      <table>
	<tr class="away-row">
	  <td>
	    <a href="${game_url}">${away_txt}</a>
	  </td>
	  %if odds.favored_id == game.away_id:
	  <td>
	    -${odds.spread}
	    <input type="button" class="action-button" id="${favored_id}" href="${favored_url}" value="bet">
	  </td>
	  %else:
	  <td>
	    ${odds.spread}
	    <input type="button" class="action-button" id="${underdog_id}" href="${underdog_url}" value="bet">
	  </td>
	  %endif
	</tr>
	<tr class="home-row">
	  <td>
	    <a href="${game_url}">${home_txt}</a>
	  </td>
	  %if odds.favored_id == game.home_id:
	  <td>
	    -${odds.spread}
	    <input type="button" class="action-button" id="${favored_id}" href="${favored_url}" value="bet">
	  </td>
	  %else:
	  <td>
	    ${odds.spread}
	    <input type="button" class="action-button" id="${underdog_id}" href="${underdog_url}" value="bet">
	  </td>
	  %endif
	</tr>
      </table>
    </div>
  </div>
</div>
