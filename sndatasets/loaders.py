"""
sndatasets : Download and normalize published SN photometric data.
"""

from __future__ import print_function

from collections import OrderedDict
import os
from os.path import join

import numpy as np
import sncosmo
from astropy.io import ascii
from astropy.table import Table, join as tabjoin

from .dlutils import download_file, download_sn_positions
from .utils import (hms_to_deg, sdms_to_deg, pivot_table,
                    mag_to_flux, jd_to_mjd, sxhr_to_deg, sx_to_deg)


CDS_PREFIX = "http://cdsarc.u-strasbg.fr/vizier/ftp/cats/"


__all__ = ["load_kowalski08", "load_hamuy96", "load_krisciunas",
           "load_csp"]


def load_kowalski08():
    """
    Nearby 99 set from Kowalski et al 2008
    http://adsabs.harvard.edu/abs/2008ApJ...686..749K
    """
    
    readme = download_file(CDS_PREFIX + "J/ApJ/686/749/ReadMe", "kowalski08")
    table1 = download_file(CDS_PREFIX + "J/ApJ/686/749/table1.dat",
                           "kowalski08")
    table10 = download_file(CDS_PREFIX + "J/ApJ/686/749/table10.dat",
                            "kowalski08")

    # Parse SN coordinates and redshifts
    meta = ascii.read(table1, format='cds', readme=readme)
    ra = hms_to_deg(meta['RAh'], meta['RAm'], meta['RAs'])
    dec = sdms_to_deg(meta['DE-'], meta['DEd'], meta['DEm'], meta['DEs'])

    data = ascii.read(table10, format='cds', readme=readme)
    data = data.filled(0.)  # convert from masked table

    data = pivot_table(data, 'band', ['{}mag', 'e_{}mag'],
                       ['B', 'V', 'R', 'I'])
    data = data[data['mag'] != 0.]  # eliminate missing values

    # Join telescope and band into one column
    data['band'] = np.char.add(np.char.replace(data['Tel'], ' ', '_'),
                               np.char.add('_', data['band']))
    del data['Tel']

    # Split up table into one table per SN and add metadata.
    sne = OrderedDict()
    for i in range(len(meta)):
        name = meta['SN'][i]
        sndata = data[data['SN'] == name]
        snmeta = OrderedDict([('name', name),
                              ('dataset', 'kowalski08'),
                              ('z_helio', meta['z'][i]),
                              ('ra', ra[i]),
                              ('dec', dec[i])])
        zp = 29. * np.ones(len(sndata), dtype=np.float64)
        zpsys = len(sndata) * ['vega']
        flux, fluxerr = mag_to_flux(sndata['mag'], sndata['e_mag'], zp)
        sne[name] = Table([jd_to_mjd(sndata['JD']), sndata['band'],
                           flux, fluxerr, zp, zpsys],
                          names=('time', 'band', 'flux', 'fluxerr', 'zp',
                                 'zpsys'),
                          meta=snmeta)
        # TODO: correct descriptions on table columns.

    return sne

def load_hamuy96():
    """Hamuy et al. 1996 AJ 112 2408 "Calan Tololo" sample
    http://adsabs.harvard.edu/abs/1996AJ....112.2408H

    Photometry has been corrected to Bessell filters.

    Position and heliocentric redshift metadata is hard-coded.
    """

    readme = download_file(CDS_PREFIX + "J/AJ/112/2408/ReadMe", "hamuy96")
    table4 = download_file(CDS_PREFIX + "J/AJ/112/2408/table4.dat", "hamuy96")

    # TODO authoritative source for this metadata?
    # NOTE: commented-out lines are SNe not in the phtometric data table.
    #                  ra             dec            z_helio
    meta = {'1990O':  ('17:15:35.92', '+16:19:25.8', 0.0303),
            '1990T':  ('19:59:02.28', '-56:15:30.0', 0.0404),
            '1990Y':  ('03:37:22.64', '-33:02:40.1', 0.0391),
            '1990af': ('21:34:58.12', '-62:44:07.4', 0.0506),
            '1991S':  ('10:29:27.79', '+22:00:46.4', 0.0546),
            '1991U':  ('13:23:22.20', '-26:06:28.7', 0.0317),
            '1991ag': ('20:00:08.65', '-55:22:03.4', 0.0141),
            '1992J':  ('10:09:00.30', '-26:38:24.4', 0.0446),
            '1992K':  ('13:10:04.20', '-46:26:30.3', 0.0103),
            #'1992O':  ('19:23:42.29', '-62:49:30.1', 0.037),
            '1992P':  ('12:42:48.95', '+10:21:37.5', 0.0252),
            '1992ae': ('21:28:17.66', '-61:33:00.0', 0.0752),
            '1992ag': ('13:24:10.12', '-23:52:39.3', 0.0249),
            #'1992ai': ('01:29:08.04', '-32:16:30.0', -1.0),
            '1992al': ('20:45:56.45', '-51:23:40.0', 0.0146),
            '1992aq': ('23:04:34.76', '-37:20:42.1', 0.1018),
            '1992au': ('00:10:40.27', '-49:56:43.3', 0.0614),
            '1992bc': ('03:05:17.28', '-39:33:39.7', 0.0202),
            '1992bg': ('07:41:56.53', '-62:31:08.8', 0.0352),
            '1992bh': ('04:59:27.55', '-58:49:44.2', 0.0450),
            '1992bk': ('03:43:01.90', '-53:37:56.8', 0.0581),
            '1992bl': ('23:15:13.25', '-44:44:34.5', 0.0437),
            '1992bo': ('01:21:58.44', '-34:12:43.5', 0.0189),
            '1992bp': ('03:36:37.95', '-18:21:13.7', 0.0793),
            '1992br': ('01:45:44.83', '-56:05:57.9', 0.0882),
            '1992bs': ('03:29:27.20', '-37:16:18.9', 0.0637),
            '1993B':  ('10:34:51.38', '-34:26:30.0', 0.0696),
            '1993H':  ('13:52:50.34', '-30:42:23.3', 0.0239),
            '1993M':  ('19:13:01.53', '-64:17:28.3', 0.090),
            '1993O':  ('13:31:07.87', '-33:12:50.5', 0.0510),
            #'1993T':  ('23:10:54.09', '-44:58:48.6', 0.088),
            #'1993af': ('05:08:00.71', '-37:29:18.0', 0.0034),
            '1993ag': ('10:03:35.00', '-35:27:47.6', 0.0490),
            '1993ah': ('23:51:50.27', '-27:57:47.0', 0.0297)}

    data = ascii.read(table4, format='cds', readme=readme)
    data = data.filled(0.)

    data = pivot_table(data, 'band', ['{}mag', 'e_{}mag'],
                       ['B', 'V', 'R', 'I'])
    data = data[data['mag'] != 0.]  # eliminate missing values

    # Split up table into one table per SN and add metadata.
    sne = OrderedDict()
    for name in meta:
        snmeta = OrderedDict([('name', name),
                              ('dataset', 'hamuy96'),
                              ('z_helio', meta[name][2]),
                              ('ra', sxhr_to_deg(meta[name][0])),
                              ('dec', sx_to_deg(meta[name][1]))])

        sndata = data[data['SN'] == name]            
        time = jd_to_mjd(sndata['HJD'])
        band = np.char.add('bessell', np.char.lower(sndata['band']))
        zp = 29. * np.ones(len(sndata), dtype=np.float64)
        zpsys = len(sndata) * ['vega']
        flux, fluxerr = mag_to_flux(sndata['mag'], sndata['e_mag'], zp)

        sne[name] = Table([time, band, flux, fluxerr, zp, zpsys],
                          names=('time', 'band', 'flux', 'fluxerr', 'zp',
                                 'zpsys'),
                          meta=snmeta)

    return sne


def load_krisciunas():
    """Load the following SNe:

    1999aa 2000ApJ...539..658K Table 2
    1999cl 2000ApJ...539..658K Table 4
    1999cp 2000ApJ...539..658K Table 4

    Photometry has been corrected to Bessell filters.
    """

    from pkg_resources import resource_stream

    sne = {}

    # Metadata
    z_helio = OrderedDict([("1999aa", 0.014443),
                           ("1999cc", 0.031328),
                           ("1999cl", 0.007609),
                           ("1999cp", 0.009480),
                           ("1999da", 0.012695),
                           ("1999dk", 0.014960),
                           ("1999ek", 0.017522),
                           ("1999gp", 0.026745),
                           ("2000bh", 0.022809),
                           ("2000bk", 0.025444),
                           ("2000ca", 0.023616),
                           ("2000ce", 0.016305),
                           ("2000cf", 0.036425),
                           ("2001ba", 0.029557),
                           ("2001bt", 0.014637),
                           ("2001cn", 0.015154),
                           ("2001cz", 0.015489),
                           ("2001el", 0.003896),
                           ("2002bo", 0.004240)])

    # Get positions
    posfname = download_sn_positions(z_helio.keys(),
                                     join('krisciunas', 'positions.csv'))
    


    # krsciunas00
    for name, fname in [('1999aa', 'table2.txt'),
                        ('1999cl', 'table4.txt'),
                        ('1999cp', 'table6.txt')]:
        f = resource_stream(__name__, join('data', 'krisciunas00', fname))
        data = ascii.read(f, format='fixed_width_no_header',
                          names=('time', 'v', 'v_err', 'b-v', 'b-v_err',
                                 'v-r', 'v-r_err', 'v-i', 'v-i_err'),
                          col_starts=(0, 21, 29, 36, 44, 51, 59, 66, 74),
                          col_ends=(7, 26, 33, 41, 48, 56, 63, 71, 78))

        data['vmag'] = data['v']
        data['vmag_err'] = data['v_err']
        data['bmag'] = data['b-v'] + data['v']
        data['bmag_err'] = np.sqrt(data['b-v_err']**2 + data['v_err']**2)
        data['rmag'] = data['v'] - data['v-r']
        data['rmag_err'] = np.sqrt(data['v-r_err']**2 + data['v_err']**2)
        data['imag'] = data['v'] - data['v-i']
        data['imag_err'] = np.sqrt(data['v-i_err']**2 + data['v_err']**2)
        for colname in ['v', 'v_err', 'b-v', 'b-v_err', 'v-r', 'v-r_err', 'v-i', 'v-i_err']:
            del data[colname]

        if data.masked:
            data = data.filled(-100.)

        data = pivot_table(data, 'band', ['{}mag', '{}mag_err'],
                           ['b', 'v', 'r', 'i'])
#                           colfmts_replace=['mag', 'magerr'],
#                           values_replace=['bessellb', 'bessellv',
#                                           'bessellr', 'besselli'])

        data = data[data['mag'] != -100.]  # eliminate missing values

        snmeta = OrderedDict([('name', name),
                              ('dataset', 'krisciunas'),
                              ('z_helio', z_helio[name]),
                              ('ra', 0.),  # TODO: fill in ra from file
                              ('dec', 0.)])  # TODO: fill in dec from file

        time = data['time'] + 2451000.0
        band = np.char.add('bessell', data['band'])
        zp = 29. * np.ones(len(data), dtype=np.float64)
        zpsys = len(data) * ['vega']
        flux, fluxerr = mag_to_flux(data['mag'], data['mag_err'], zp)

        sne[name] = Table([time, band, flux, fluxerr, zp, zpsys],
                          names=('time', 'band', 'flux', 'fluxerr', 'zp',
                                 'zpsys'),
                          meta=snmeta)

    return sne

def load_csp():
    """CSP DR2 Photometry from Stritzinger et al 2011
    http://adsabs.harvard.edu/abs/2011AJ....142..156S """
    
    prefix = CDS_PREFIX + 'J/AJ/142/156/'
    readme = download_file(prefix + 'ReadMe', 'csp')
    table1 = download_file(prefix + 'table1.dat', 'csp')  # general
    table4 = download_file(prefix + 'table4.dat', 'csp')  # optical
    table5 = download_file(prefix + 'table5.dat', 'csp')  # ir
    
    meta = ascii.read(table1, format='cds', readme=readme)
    ra = hms_to_deg(meta['RAh'], meta['RAm'], meta['RAs'])
    dec = sdms_to_deg(meta['DE-'], meta['DEd'], meta['DEm'], meta['DEs'])
    
    opt_data = ascii.read(table4, format='cds', readme=readme)
    ir_data = ascii.read(table5, format='cds', readme=readme)
    data = tabjoin(opt_data, ir_data, join_type='outer')

    data = data.filled(0.)  # copying this from kyle

    data = pivot_table(data, 'band', ['{}mag', 'e_{}mag'],
                       ['u', 'g', 'r', 'i', 'B', 'V', 
                        'Y', 'J', 'H', 'K'])

    data = data[data['mag'] != 0]  # eliminate missing values

    bandtel = zip(data['band'], data['Tel'])
    ir = ['Y', 'J', 'H']
    
    data['filter'] = ['csp' + b if b not in ir  else 'csp' + b + t[0] \
                          for (b, t) in bandtel]
    data['filter'] = [f.lower() for f in data['filter']]
    del data['Tel'], data['band'], data['---'], data['f_JD']

    def _which_V(mjd):
        # return the CSP V band that was in use on mjd.
        if mjd < 53748:
            ans = '3014'
        elif mjd > 53761:
            ans = '9844'
        else:
            ans = '3009'
            return 'cspv' + ans
        
    data['filter'] = [_which_V(jd_to_mjd(t)) if 'v' in b else b \
                          for (b, t) in zip(data['filter'], data['JD'])]

    sne = OrderedDict()
    magsys = sncosmo.get_magsystem('csp')
    for i in range(len(meta)):
        name = meta['SN'][i]
        sndata = data[data['SN'] == name]
        snmeta = OrderedDict([('name', name),
                              ('dataset', 'csp'),
                              ('z_helio', meta['z'][i]),
                              ('ra', ra[i]),
                              ('dec', dec[i])])
        zpsys = len(sndata) * ['csp']
        zp = [magsys.offsets[magsys.bands.index(sncosmo.get_bandpass(b))] \
                  for b in data['filter']]
        flux, fluxerr = mag_to_flux(sndata['mag'], sndata['e_mag'], zp)
        sne[name] = Table([jd_to_mjd(sndata['JD']), sndata['filter'],
                           flux, fluxerr, zp, zpsys],
                          names=('time', 'band', 'flux', 'fluxerr', 'zp',
                                 'zpsys'),
                          meta=snmeta)
    return sne
    
