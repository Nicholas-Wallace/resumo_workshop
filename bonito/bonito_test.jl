using Bonito
using WGLMakie 
using SegyIO
import WGLMakie as W
import Bonito.TailwindDashboard as D
using Statistics

# lê um arquivo segy com um certo range de cdp e retorna:
# amplitudes, numero de amostras e duração total(s)
 
#= function read_data(filename::String, cdp_range)
    block = segy_read(filename) 

    #cdps = [h.CDP for h in block.traceheaders]
    #mask = [cdp in cdp_range for cdp in cdps]
    #indices = findall(mask)

    amplitudes = Float32.(block.data)

    return amplitudes, block.fileheader.bfh.ns,  block.fileheader.bfh.dt/1000

end =#
#Bonito.browser_display()

function read_data(filename::String)
    keys = ["TraceNumber"]
    scan = scan_file("/home/nicholas/code-test/resumo_workshop/streamlit/data/"*filename, keys, 100)

    #block = read_con(scan, 1:size(scan)[1])
    block = read_con(scan, 1:size(scan)[1])

    return Float32.(block.data), block.fileheader.bfh.ns,  block.fileheader.bfh.dt/1000

end

function perc_slider()
    s = Bonito.Slider(90:100; value=100)
    return s
end

function apply_button(actual_perc_rate, perc_rate)
    btn = Button("Apply")
    on(btn.value) do _
        actual_perc_rate[] = perc_rate.val 
        println("apply")
    end
    return btn
end

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

#function otimizar_plot(size, t, traces, amplitudes)

#end

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


#WGLMakie.activate!(; screen_config...)
WGLMakie.activate!(; use_html_widgets = true)

app = App() do session

    actual_perc_rate = Observable(100)

    current_cmap = Observable(:balance)
    
    amplitudes, ns, dt = read_data("jequitinhonha.sgy")

    controls = colormap_buttons(current_cmap)
    s = perc_slider()
    button_apply = apply_button(actual_perc_rate, s.value)

    @show actual_perc_rate

    return DOM.div(
        colormap_buttons(current_cmap),
        DOM.div(s, s.value, button_apply),
        makie_plot(amplitudes, current_cmap, actual_perc_rate),
        style="""
            display:flex;
            justify-content: center;
        """
    )
end

server = Server(app, "0.0.0.0", 8080)
Bonito.route!(server, "/" => app)

wait(server)