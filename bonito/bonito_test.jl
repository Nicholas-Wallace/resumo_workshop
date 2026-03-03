using Bonito
using WGLMakie 
using SegyIO
import WGLMakie as W
using BenchmarkTools

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

    block = read_con(scan, 1:50)

    return Float32.(block.data), block.fileheader.bfh.ns,  block.fileheader.bfh.dt/1000

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

function makie_plot(filename, current_cmap)
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

    amplitudes, ns, dt = read_data(filename)
    max_amp = maximum(abs,amplitudes)
    amplitudes = amplitudes / max_amp

    max_amp = maximum(amplitudes)
    min_amp = minimum(amplitudes)

    amplitudes = amplitudes'
    traces = collect(1:size(amplitudes)[1])
    t = collect(range(0, dt, size(amplitudes)[2]))

    

    y = t
    x = traces 
    z = amplitudes

    heatmap!(ax, Resampler(amplitudes),
        colormap = current_cmap, 
        colorrange = (min_amp, max_amp),
        interpolate = true
        )

    @show ax.limits

    Colorbar(f[1, 2], colormap=current_cmap,
        labelsize = 14,
        ticklabelsize = 14,
        width = 30, # thickness
        tellheight = true 
    )

    return f

end


#WGLMakie.activate!(; screen_config...)
WGLMakie.activate!(; use_html_widgets = true)

app = App() do session

    current_cmap = Observable(:balance)

    controls = colormap_buttons(current_cmap)

    

    return DOM.div(
        colormap_buttons(current_cmap),
        makie_plot("0258-6089.sgy", current_cmap),
        style="""
            display:flex;
            justify-content: center;
        """
    )
end

server = Server(app, "0.0.0.0", 8080)
Bonito.route!(server, "/" => app)

wait(server)