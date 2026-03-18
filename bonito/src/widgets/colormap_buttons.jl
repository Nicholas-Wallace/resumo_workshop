export colormap_buttons

function colormap_buttons(cmap_obs)
    options = [:balance, :grayC50]

    buttons = map(options) do name
        btn = Button(String(name))
        on(btn.value) do _
            cmap_obs[] = name
        end
        return btn
    end

    return DOM.div(DOM.h1("colormaps:"), buttons...)
end