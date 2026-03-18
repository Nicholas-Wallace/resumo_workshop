export makie_plot

function makie_plot(amplitudes, current_cmap, perc_rate)
    f = Figure(size=(2*600, 2*450))
    ax = Axis(f[1, 1],
        title = "seismic_section",
        titlesize = 24,
        xlabel = "trace",
        ylabel = "time(s)",
        xlabelsize = 18,
        ylabelsize = 18,
        xticklabelsize = 18,
        yticklabelsize = 18,
        yreversed = true,         
        xgridvisible = false,      
        ygridvisible = false,
        zoombutton=Keyboard.left_control
    )
    
    amplitudes = amplitudes / maximum(abs, amplitudes)
    amplitudes = collect(Matrix{Float32}(amplitudes'))

    display_data = Observable(amplitudes)

    resampled_data = lift(display_data) do data
        return Resampler(data)
    end

    on(perc_rate) do val
        dr = vec(amplitudes)
        perc_val = quantile(dr, perc_rate.val/100)
        
        display_data[] = (clamp.(amplitudes, -perc_val, perc_val))/perc_val
        println("Got an update: ", val)

    end

    heatmap!(ax, resampled_data,
        colormap = current_cmap, 
        colorrange = (-1, 1),
        interpolate = true
        )

    Colorbar(f[1, 2], colormap=current_cmap,
        labelsize = 14,
        ticklabelsize = 14,
        width = 30, # thickness
        tellheight = true 
    )

    on(events(ax).keyboardbutton) do event
        if event.action == Keyboard.press || event.action == Keyboard.repeat
            if event.key == Keyboard.left_control
                println("pressed")
                reset_limits!(ax)
            end
        end
    end

    return f

end