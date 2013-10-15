<div class="widget-bet-total">
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
    <% under_id = 'underover-{}-under'.format(game_id) %>
    <% under_url = mkurl(broute, context='betunder', id=game_id) %>
    <% over_id = 'underover-{}-over'.format(game_id) %>
    <% over_url = mkurl(broute, context='betover', id=game_id) %>
    <% form_url = mkurl('vig_betfrag', context='betover', id='foo') %>
    <a href="${game_url}">${summary}</a><br>
    <div class="underover-table">
      <table>
	<tr class="over-row">
	  <td>
	    over ${odds.total}
	    <input type="button" class="action-button" id="${over_id}" href="${over_url}" value="bet">
	  </td>
	</tr>
	<tr class="under-row">
	  <td>
	    under ${odds.total}
	    <input type="button" class="action-button" id="${under_id}" href="${under_url}" value="bet">
	  </td>
	</tr>
      </table>
    </div>
  </div>
</div>

