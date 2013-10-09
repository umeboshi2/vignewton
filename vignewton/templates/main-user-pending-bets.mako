<div class="main-user-pending-bets-view">
  <div class="listview-header">
    <p>Pending Bets</p>
  </div>
  %for bet in bets:
  <div class="listview-list">
    <div class="listview-list-entry">
      Bet ${bet.amount}(${bet.bet_type})on ${bet.game.summary}
    </div>
  </div>
  %endfor
</div>

