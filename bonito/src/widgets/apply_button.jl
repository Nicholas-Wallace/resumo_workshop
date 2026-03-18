export apply_button

function apply_button(actual_perc_rate, perc_rate)
    btn = Button("Apply")
    on(btn.value) do _
        actual_perc_rate[] = perc_rate.val 
        println("apply")
    end
    return btn
end