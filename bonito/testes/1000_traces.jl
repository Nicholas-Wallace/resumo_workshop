
# teste lendo 1000 traços de uma vez com o arquivo de 1.5 GB
function read_data(filename::String)
    keys = ["CDP"]
    scan = segy_scan("/home/nicholas/code-test/resumo_workshop/testes/data", "0258-6112A.sgy", keys)

    #cdps = [blocks.summary["CDP"][1] for blocks in scan.blocks]
    #mask = [cdp in cdp_range for cdp in cdps]
    #indices = findall(mask)

    block = read_con(scan, 1:1000)
    amplitudes = Float32.(block.data)

    return amplitudes, block.fileheader.bfh.ns,  block.fileheader.bfh.dt/1000

end

function makie_plot(filename)
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

    amplitudes, ns, dt = read_data(filename)
    max_amp = maximum(abs,amplitudes)
    norm_amplitudes = amplitudes / max_amp

    max_amp = maximum(norm_amplitudes)
    min_amp = minimum(norm_amplitudes)

    y = collect(range(0, dt, size(amplitudes)[2]))
    x = collect(1:size(amplitudes)[1])
    z = norm_amplitudes'

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

    return f

end
