$(document).ready ->
        $('.betgame-window').hide()
        
        $('#confirm-bet-button').click ->
                btnid = $(this).attr('id')
                betlist = btnid.split('-')
                bettype = betlist[0]
                game_id = new Number(betlist[1])
                url = $('#confirm-url').val()
                $('header > h2').text("$$$$$$$" + url)
                # I can't remember how to load another
                # url, so I'm using a hacky form submit
                # 
                #$(window).load(url)
                #form = document.createElement('form')
                #form.setAttribute('method', 'post')
                #form.setAttribute('action', url)
                #form.submit()
                #$(:window).load(url)
                window.location = url
                
        $('#nothere').click ->
                betval = betlist[2]
                betwin_id = "betgame-window-" + game_id
                betwin_id_sel = "#" + betwin_id
                $(betwin_id_sel).text("Bet on this game")
                betwin_visible = $(betwin_id_sel).is(":visible")
                $('header > h2').text(betwin_visible)
                if betwin_visible
                        $(betwin_id_sel).hide()
                else
                        $(betwin_id_sel).show()

                
                         
                
