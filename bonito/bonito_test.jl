using Bonito
using WGLMakie 
using SegyIO
import WGLMakie as W
using BenchmarkTools

# lê um arquivo segy com um certo range de cdp e retorna:
# amplitudes, numero de amostras e duração total(s)
 
function read_data(filename::String, cdp_range)
    block = segy_read(filename) 

    #cdps = [h.CDP for h in block.traceheaders]
    #mask = [cdp in cdp_range for cdp in cdps]
    #indices = findall(mask)

    amplitudes = Float32.(block.data)

    return amplitudes, block.fileheader.bfh.ns,  block.fileheader.bfh.dt/1000

end


function makie_plot(cmap::Observable)
    f = Figure()
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
        ygridvisible = false
    )

    amplitudes, ns, dt = read_data("0258-6112A.sgy", 640:840)
    max_amp = maximum(abs,amplitudes)
    norm_amplitudes = amplitudes / max_amp

    max_amp = maximum(norm_amplitudes)
    min_amp = minimum(norm_amplitudes)

    @show max_amp
    @show min_amp

    y = collect(range(0, dt, size(amplitudes)[2]))
    x = collect(1:size(amplitudes)[1])
    z = norm_amplitudes'

    heatmap!(ax, x, y, z,
        colormap = cmap, 
        colorrange = (min_amp, max_amp),
        interpolate = true
        )

    Colorbar(f[1, 2], cmap,
        labelsize = 14,
        ticklabelsize = 14,
        width = 30, # thickness
        tellheight = true 
    )

    #@show z

    return f

end

function colormap_buttons(cmap_obs)
    options = [:balance, :viridis]

    buttons = map(options) do name
        btn = Button(String(name))
        on(btn.value) do _
            cmap_obs[] = name
        end
        return btn
    end

    return DOM.div(DOM.h1("colormaps:"), buttons...)
end

function plot_button(plot_container)
    button = Button("Click me")
    on(button.value) do click::Bool
        duration = @elapsed begin
        f = Figure()
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
            ygridvisible = false
        )

        filename = "0258-6089.sgy"

        amplitudes, ns, dt = read_data(filename, 1700:1800)
        max_amp = maximum(abs,amplitudes)
        norm_amplitudes = amplitudes / max_amp
        norm_amplitudes = Matrix(norm_amplitudes')

        max_amp = maximum(norm_amplitudes)
        min_amp = minimum(norm_amplitudes)

        t = collect(range(0, dt, size(norm_amplitudes)[2]))

        @show size(norm_amplitudes)

        y = Observable(t)
        x = Observable(collect(1:size(norm_amplitudes)[1]))
        z = Observable(norm_amplitudes)

        heatmap!(ax, x, y, z,
            colormap = :balance, 
            colorrange = (min_amp, max_amp),
            interpolate = true
            )

        Colorbar(f[1, 2], colormap=:balance,
            labelsize = 14,
            ticklabelsize = 14,
            width = 30, # thickness
            tellheight = true 
        )

        plot_container[] = f

        end
        @show round(duration, digits=4)    

    end
    return button
end

#WGLMakie.activate!(; screen_config...)

app = App() do session

    #current_cmap = Observable(:balance)

    #controls = colormap_buttons(current_cmap)

    # f = Figure()
    # ax = Axis(f[1, 1],
    #     title = "seismic_section",
    #     titlesize = 24,
    #     xlabel = "trace",
    #     ylabel = "time(s)",
    #     xlabelsize = 18,
    #     ylabelsize = 18,
    #     xticklabelsize = 18,
    #     yticklabelsize = 18,
    #     yreversed = true,         
    #     xgridvisible = false,      
    #     ygridvisible = false
    # )

    # amplitudes, ns, dt = read_data("jequitinhonha.sgy", 1700:1800)
    # max_amp = maximum(abs,amplitudes)
    # norm_amplitudes = amplitudes / max_amp
    # norm_amplitudes = Matrix(norm_amplitudes')

    # max_amp = maximum(norm_amplitudes)
    # min_amp = minimum(norm_amplitudes)

    # t = collect(range(0, dt, size(norm_amplitudes)[2]))

    # #@show size(norm_amplitudes)

    # y = Observable(t)
    # x = Observable(collect(1:size(norm_amplitudes)[1]))
    # z = Observable(norm_amplitudes)

    # heatmap!(ax, x, y, z,
    #     colormap = current_cmap, 
    #     colorrange = (min_amp, max_amp),
    #     interpolate = true
    #     )

    # Colorbar(f[1, 2], colormap=current_cmap,
    #     labelsize = 14,
    #     ticklabelsize = 14,
    #     width = 30, # thickness
    #     tellheight = true 
    # )

    # delta_time = t[2] - t[1]

    # trace_start = 1
    # trace_end = size(amplitudes)[1]

    # #time_start = 1
    # time_end = size(amplitudes)[2]

    # on(ax.finallimits) do limits
    #     # ajeitar a questão dos limites

    #     x_start, y_start = limits.origin
    #     x_width, y_width = limits.widths

    #     @show y_start
    #     @show y_width

    #     @show typeof(limits.origin)

    #     x_end = x_start + x_width
    #     y_end = y_start + y_width

    #     trace_start = Int(floor(x_start))        
    #     trace_end = Int(ceil(x_end))

    #     time_start = Int(floor(y_start/delta_time)) + 1
    #     time_end = Int(ceil(y_end/delta_time)) + 1

    #     # o eixo y ainda não está 100% 
        
    #     try
    #         z[] = norm_amplitudes[trace_start:trace_end, time_start:time_end]
    #         x[] = collect(trace_start:trace_end)
    #         y[] = t[time_start:time_end]

    #         #@show t[time_start:time_end]
    #     catch e
    #         @show e 
    #     end


    # end

    # #deregister_interaction!(ax, :rectanglezoom)
    # #deregister_interaction!(ax, :scrollzoom)

    # register_interaction!(ax, :my_interaction) do event::ScrollEvent, Axis
    #     println("You scrolled yhe mouse")
    # end

    plot_container = Observable{Any}(DOM.div("click the button to plot"))

    return DOM.div(
        DOM.h1("sessão sismica"), 
        plot_button(plot_container),
        plot_container
    )
end

server = Server(app, "0.0.0.0", 8080)
Bonito.route!(server, "/" => app)

wait(server)