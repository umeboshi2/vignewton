<div class="admin-view-accounts-view">
     <p>Pending Bets</p>
  <% dtformat = '%b %d %Y - %H:%M:%S' %>
  %for bet in bets:
  <div class="listview-header">
  </div>
  <div class="listview-list">
    <div class="listview-list-entry">
      ${bet.user.username} - ${bet.game} - ${bet.amount} - ${bet.bet_type}
    </div>
  </div>
  %endfor
</div>

