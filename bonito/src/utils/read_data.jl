export read_data

function read_data(filename::String)
    keys = ["TraceNumber"]
    scan = scan_file("/home/nicholas/code-test/resumo_workshop/streamlit/data/"*filename, keys, 100)

    #block = read_con(scan, 1:size(scan)[1])
    block = read_con(scan, 1:size(scan)[1])

    return Float32.(block.data), block.fileheader.bfh.ns,  block.fileheader.bfh.dt/1000

end