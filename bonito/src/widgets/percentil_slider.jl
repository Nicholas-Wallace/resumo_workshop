export percentil_slider

function percentil_slider()
    s = Bonito.Slider(90:100; value=100)

    on(s.value) do value
        @show value
    end

    return s
end