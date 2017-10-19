# =============================================================================================
# Copyright 2017 dgketchum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================================

import os
from pprint import pprint


def get_lathuille_variables():
    variables = {'NEE_f': None,
                 'NEE_f_delta': None,
                 'GPP_f': None,
                 'GPP_f_delta': None,
                 'Reco': None,
                 'NEE_GPP_fqcOK': None,
                 'LE_f': None,
                 'LE_fqcOK': None,
                 'H_f': None,
                 'H_fqcOK': None,
                 'G_f': None,
                 'G_fqcOK': None,
                 'Ta_f': None,
                 'Ta_fqcOK': None,
                 'Ts1_f': None,
                 'Ts1_fqcOK': None,
                 'Ts2_f': None,
                 'Ts2_fqcOK': None,
                 'VPD_f': None,
                 'VPD_fqcOK': None,
                 'Precip_f': None,
                 'Precip_fqcOK': None,
                 'SWC1_f': None,
                 'SWC1_fqcOK': None,
                 'SWC2_f': None,
                 'SWC2_fqcOK': None,
                 'WS_f': None,
                 'WS_fqcOK': None,
                 'Rg_f': None,
                 'Rg_fqcOK': None,
                 'PPFD_f': None,
                 'PPFD_fqcOK': None,
                 'Rn_f': None,
                 'Rn_fqcOK': None,
                 'Rg_pot': None,
                 'Rd': None,
                 'Rd_qcOK': None,
                 'Rr': None,
                 'Rr_qcOK': None,
                 'PPFDbc': None,
                 'PPFDbc_qcOK': None,
                 'PPFDd': None,
                 'PPFDd_qcOK': None,
                 'PPFDr': None,
                 'PPFDr_qcOK': None,
                 'FAPAR': None,
                 'FAPAR_qcOK': None,
                 'LWin': None,
                 'LWin_qcOK': None,
                 'LWout': None,
                 'LWout_qcOK': None,
                 'SWin': None,
                 'SWin_qcOK': None,
                 'SWout': None,
                 'SWout_qcOK': None,
                 'H2Ostor1': None,
                 'H2Ostor2': None,
                 'Reco_E0_100': None,
                 'Reco_E0_200': None,
                 'Reco_E0_300': None,
                 'wdef_cum': None,
                 'wbal_clim': None,
                 'wbal_act': None,
                 'Drain': None,
                 'NEE_mor_f': None,
                 'NEE_mid_f': None,
                 'NEE_aft_f': None,
                 'GPP_mor_f': None,
                 'GPP_mid_f': None,
                 'GPP_aft_f': None,
                 'Ecov_mor_f': None,
                 'Ecov_mid_f': None,
                 'Ecov_aft_f': None,
                 'gsurf_mor_f': None,
                 'gsurf_mid_f': None,
                 'gsurf_aft_f': None,
                 'H_mor_f': None,
                 'H_mid_f': None,
                 'H_aft_f': None,
                 'Tair_min_f': None,
                 'Tair_max_f': None,
                 'NEE_night_f': None,
                 'NEE_midnight_f': None,
                 'VPDday_f': None,
                 'EpotPT_day_viaRn': None,
                 'WUE_GPP': None,
                 'WUE_NEE': None,
                 'RUE_GPP': None,
                 'RUE_NEE': None,
                 'b_GPP_Ecov': None,
                 'b_NEE_Ecov': None,
                 'a_GPP_Ecov': None,
                 'a_NEE_Ecov': None,
                 'a_sig_GPP_Ecov': None,
                 'a_sig_NEE_Ecov': None,
                 'b_GPP_Rg': None,
                 'b_NEE_Rg': None,
                 'a_GPP_Rg': None,
                 'a_NEE_Rg': None,
                 'a_sig_GPP_Rg': None,
                 'a_sig_NEE_Rg'
                 'Precip8': None,
                 'Precip30': None,
                 'Precip60': None,
                 'wbal_act8': None,
                 'wbal_act30': None,
                 'wbal_act60': None,
                 'Epot_viaLE_H': None,
                 'EpotPT_viaLE_H': None,
                 'Epot_viaRg': None,
                 'Epot_viaRn': None,
                 'Epot_f': None,
                 'Epot_flag': None,
                 'gsurf_viaRg': None,
                 'gsurf_viaRn': None,
                 'gsurf_viaLE_H': None,
                 'gsurf_f': None,
                 'gsurf_flag': None,
                 'EpotPT_viaRn': None,
                 'H2Ostor1_hWHC': None,
                 'H2Ostro2_hWHC': None,
                 'Drain_hWHC': None}

    pprint(variables)
    return variables


if __name__ == '__main__':
    home = os.path.expanduser('~')

# ========================= EOF ====================================================================
