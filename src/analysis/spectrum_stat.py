import xarray as xr
import data_loader
import numpy as np
import PentadTools as ptt


datasets = [ "oisst", ]
tp_rng = [ "1982P01", "1983P01" ]
label = "NPAC_spec-lon"

wvlen_bnds = [ 
    [0, 2], 
    [2, 5], 
    [5, 360], 
]


def work(
    dataset,
    varname,
    tp_rng,
    label,
):

    

    #print("Doing tp_rng = [ %s, %s ]" % (tp_rng[0], tp_rng[1], ))

    ds = data_loader.load_dataset(
        dataset = dataset,
        datatype = "spectral",
        varname = varname,
        tp_beg = tp_rng[0],
        tp_end = tp_rng[1],
        label = label,
        inclusive = "both",
    )

    #print(ds)
    #print("wvlen = ", ds.coords["wvlen"].to_numpy()) 


    data_vars = dict()
 
    variance = ds["dftcoe_form2"].sel(complex_radiphas="radius")**2
    total_variance = variance.sum(dim="wvlen")
   
    # Group wvlen
    wvlen_group = ["no_group",] * len(ds.coords["wvlen"])

    for i, wvlen in enumerate(ds.coords["wvlen"].to_numpy()):
        for wvlen_beg, wvlen_end in wvlen_bnds:
            if wvlen >= wvlen_beg and wvlen < wvlen_end:
                group_name = "%d-%d" % (wvlen_beg, wvlen_end,)
                wvlen_group[i] = group_name
                break
            
    ds = xr.merge([
        ds,
        xr.DataArray(
            data = wvlen_group,
            dims = ["wvlen",],
            coords = ds.coords["wvlen"],
        ),
    ])

    variance = ds.

        ).sum(dim="wvlen", skipna=True) / total_variance
       
        sub_variance = sub_variance.rename(

        )
    
    """

    for pentadstamp in ds.coords["pentadstamp"]:

        txt = ""
        
        tp = ptt.Pentads2TimePentad(pentadstamp)
      
        _ds = ds.sel(pentadstamp=pentadstamp)
        variance = _ds["dftcoe_form2"].sel(complex_radiphas="radius")**2
        total_variance = variance.sum(dim="wvlen")
        

 
        txt += "%s : " % (tp,) 
        for wvlen_beg, wvlen_end in wvlen_bnds:
            sub_variance = variance.where(
                ( variance.coords["wvlen"] >= wvlen_beg )
                & ( variance.coords["wvlen"] < wvlen_end )
            ).sum(dim="wvlen", skipna=True) / total_variance
            
            txt += "  %03d-%03d deg = %.2f %%, " % ( wvlen_beg, wvlen_end, sub_variance * 100)
     
        print(txt)

for dataset in datasets:

    for tp in ptt.pentad_range("1982P01", "1983P01", inclusive="left"):
        work(
            dataset,
            'sst',
            [tp, tp],
            label 
        )







