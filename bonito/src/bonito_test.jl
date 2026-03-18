using Bonito
using WGLMakie 
using SegyIO
import WGLMakie as W
import Bonito.TailwindDashboard as D
using Statistics

include("widgets/percentil_slider.jl")
include("widgets/apply_button.jl")
include("widgets/colormap_buttons.jl")
include("utils/read_data.jl")
include("utils/makie_plot.jl")

#WGLMakie.activate!(; screen_config...)
WGLMakie.activate!(; use_html_widgets = true)

app = App() do session

    actual_perc_rate = Observable(100)

    current_cmap = Observable(:balance)
   
    #index_cmap = Observable(1)
    
    amplitudes, ns, dt = read_data("0258-6089.sgy")

    controls = colormap_buttons(current_cmap)
    s = percentil_slider()
    button_apply = apply_button(actual_perc_rate, s.value)

    @show actual_perc_rate

    return DOM.div(
        DOM.div(DOM.h1("percentil adjustment"), s, s.value),
        makie_plot(amplitudes, current_cmap, s.value),
        style="""
            display:flex;
            justify-content: center;
        """
    )
end

server = Server(app, "0.0.0.0", 8080)
Bonito.route!(server, "/" => app)

wait(server)