<div class="main-user-closed-bets-view">
  <div class="listview-header">
    <p>Closed Bets</p>
  </div>
  %for bet in bets:
  <div class="listview-list">
    <div class="listview-list-entry">
      <div class="bet-info">
	Bet ${bet.amount}(${bet.bet_type})on ${bet.game.summary} (${bet.status})<br>
      </div>
      <div class="place-bet-transaction">
	<div class="place-bet-header">
	  Place Bet Transaction
	</div>
	<hr>
	<div class="bet-transfer-list">
	  %for xfer in bet.bet_txn.transfers:
	  <div class="bet-transfer">
	    ${xfer.account.name} ${xfer.amount}
	  </div>
	  %endfor
	</div>
      </div>
      <div class="determine-bet-transaction">
	<div class="determine-bet-header">
	  Determine Bet Transaction
	</div>
	<hr>
	<div class="bet-transfer-list">
	  %for xfer in bet.close_txn.transfers:
	  <div class="bet-transfer">
	    ${xfer.account.name} ${xfer.amount}
	  </div>
	  %endfor
	</div>
      </div>
    </div>
  </div>
  %endfor
</div>

