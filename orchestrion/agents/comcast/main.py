import requests
import logging
import re
import json
import urllib.parse

from html.parser import HTMLParser

logger = logging.getLogger(__name__)

URL_OAUTH = "https://customer.xfinity.com/oauth/force_connect/?continue=%23%2Fdevices"
URL_USAGE = "https://customer.xfinity.com/apis/services/internet/usage"
URL_LOGIN = "https://login.xfinity.com/login"

OUTPUT_TYPE = "inbluxdb"


class ServiceModule:
    def __init__(self, config, output):
        self.interval = int(config["interval"])
        self.username = config["username"]
        self.password = config["password"]
        self.session = requests.Session()
        self.session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
                "Upgrade-Insecure-Request": "1",
                "content-type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "authority": "customer.xfinity.com",
                "referrer": "https://customer.xfinity.com",
            }
        )
        self.output = output

    def _is_security_check(self, res):
        # does url match?
        if res.url == "https://idm.xfinity.com/myaccount/security-check?execution=e1s1":
            return True
        # otherwise, try checking response text
        if "security-check" in res.text:
            return True
        return False

    def _login(self):
        logger.debug("Authentication")
        res = self.session.get(URL_OAUTH)

        if res.status_code != 200:
            logger.error(f"Failed to find reqId, status_code:{res.status_code}")
            return

        # logger.debug(res.text)

        req_id = re.search(r'<input type="hidden" name="reqId" value="(.*?)">', res.text).group(1)
        continue_url = re.search(r'<input type="hidden" name="continue" value="(.*?)">', res.text).group(1)
        client_id = re.search(r'<input type="hidden" name="client_id" value="(.*?)">', res.text).group(1)
        forceAuthn = re.search(r'<input type="hidden" name="forceAuthn" value="(.*?)">', res.text).group(1)
        s = re.search(r'<input type="hidden" name="s" value="(.*?)">', res.text).group(1)

        logger.debug(f"Found req_id = {req_id}")
        logger.debug(f"Found continue = {continue_url}")
        logger.debug(f"Found client_id = {client_id}")
        logger.debug(f"Found forceAuthn = {forceAuthn}")
        logger.debug(f"Found s = {s}")

        params = {
            "user": self.username,
            "passwd": self.password,
            "r": "comcast.net",
            "selectAccount": "false",
            "reqId": req_id,
            "deviceAuthn": "false",
            "s": s,
            "forceAuthn": "1",
            "rm": "1",
            "ipAddrAuthn": "false",
            "continue": continue_url,
            "passive": "false",
            "lang": "en",
            "client_id": client_id,
            "selectAccount": "false",
            "X-hzfdeCEGvt-f": "A6r6pop0AQAAPLJEX2-X4D95iRlBpLzdhLDiWg1k-og-XiSjCUC3A6kAC5SIAJy4FKHAfwAAHvUAAAAA",
            "X-hzfdeCEGvt-b": "-mvfwbk",
            "X-hzfdeCEGvt-c": "A_CKpop0AQAAPuMf9fu8_-g2AVP_7bNnDge2Rd8pNjLhn_FFX_foYgJHzutjAOGmu1bAf3ypMl3su1Hx",
            "X-hzfdeCEGvt-d": "o_0",
            "X-hzfdeCEGvt-z": "p",
            "X-hzfdeCEGvt-a": "B52praLhN9A_Ki-9gyTL3NFJl17cYFj2d_JfyzfHBVRD46OpTXm6jrWvhVotCrWhbz-md8zUQ1EQN_OMuk9jXO2FAcdXKqVwlWf_kO9tKGmS-cwE7yN9AXZLlvbRna2Tfk6adBHeqkCDBRogXSqnOzT-CVbfUY6=Mfk-5CTJxAKR28WTiGfufmyVv4Xo2z-hZYHsaHM3xpXF5UTeYPPwaQ9yxXBZcbXHeFM-BoRARbWA5keUf1bFl6G8Z=d6MQOo0jbA9tgTC3-eH=QUPj5sK03dmsGOmstHK=6Ez3E5ds6wuWEEeM2mi9-OO1RF5ScNLFKH1rx0zsxWaAZqaXmvxpCXjO_ncDhiCbJZXSk2tTv52Bc3Q_UAFkTPApE-69SJvBlEGFx3GsiaSTDYVlo1Jr5VyhSyR-Cqq5u62uKOm6mwwbgKhxDz9UpzrRu0WhHAT5cDXYvSbGJUvqNS=iLbSAm4B-F3qB0KJbor30=2hNpLMRPFdw7xS63OMlE56CbJzr41RX_-QPGLF9DezMUU1a2mrWUNehuzJhjRzEkk2vm2_DoJet7NdS6PQOAjpCmuxUOXdj5UG4KA-mL7fZ4iXTrKNb3k_pEiPBsQv7Mbk1aeZJA0KXasJj8BOTT7Ku9zcREENW=X4uwvRsD7FJ-qw0CxBFdqB1=3lkbX5p_=Y7JZuvDRXypsC7expdYOhyF9sxw_S9gtM-uMGoTTScurAxYQeHTFf2_EfrGmllM7f0do6sS=fTb8a_hlsw3z=HQ4EXUlMDVzq0mV8bo_iUQldm6MO8tQLRqm3n5yrxx5DGQ93PNbP-p2tHMCA7B-y_cB3YD=dcYwnuGQ_aRiM-w7NS_Y1eNQUlee9h6KfrfGzXpEodcGVRvVpFOvfyJJQJnu0cHM=OlqblK9SvvBv0CKaf7lySelSE58=vpjM8i5UmDDZinZZeX74Hl-86-xE7kZNa2AU-xwF0Orwomfvl9u1hHd8u-DXpBcAK4ePU-EueHaf8w2Kjk9ud-O8O1BLEc0GzRg540yRZoetEFv7eyaOdEUy6G7oPKNH=LbcLUh1lXHzBWyn6aOy_h1PGn9wFehsq=3A3B1pJpKKFvnXFBOfoggn0lh3LlEKrZux_kpbwkcnT4eia7Bhgmflu6Rbx0VwNVlBnKossZRf7vwOx=v4ZaMjljKar3L2ZSwl9WlvF3kC01-24AXgp7PsdXlD2MwJWUUZAiuSrMVrhxD_a7QMkF_8FQfLd1ET0_tFNyMUwAsC9R15nE5eaiLm1-TOEA_JxtFCx1NUmQzwGO75H_hfWiQ2dG9591ou0CsyvCTM5eWuy-ZjhgCMneCKKXslF-NeYT7OLbSxFL_W1yWR2fw1QDrBJgu=lzv8GsGOnVK3v=yWEgTGbSWYpuu9EBSkcBsKKARspdP=8ftUCqa1N5n1VFmMxKSpoiARdDPu7Z7lYETX-lZECAszw7RH0GRbpv39SA-cF8PC5=idXm8SqJ896w=wkb6RlS5cS3Vc70ZTh4LfezgbuOJXZp=rQmBy3owjSJayOl6qk_QgnO2j7cwr_sLE12KTbkQi=a15t5hSxMKzB_3ePPLv4xoNxmtr-xA07d52r0qQ6S1VONu3uMKDEqF4pCV=V6o5HRaxcQdXGPG1rR=h6udEBG_1U_Yj0TE8DnHo75EgqtcOi90i1VbrPuM2kRA9advd-GajLO8BlJlHgQXRVtiek-cR0kp2XhkfN5s2ZEp1ePP-uSj=8mCqi=hsy0=EwVco2mx6QfgRcqvN7YxJxKLF1wmcs1tYBxQgpnqkG1YRJZvoEaGzbB4fD0HtSvr-Ewbs=f8RgmrKVwtRukqCafERbcdS_XvD9dXielZWy_sBuHkihHQ_D7=d2daNnUV9YpYN-cCeTZiYhzjNWLlo8fS3-S1J-qrwt8kdE_Dfef3FdTj29viM7742tYBq2iHiRzu6aGQm9w9vKKW-u=Qdh4M5Xdwz4qnkunGsJ17QuHL4de0XyH2G_98YCk5sf3dUD=OSBqRnJYBeLbWVi=qFqas1F4bCXGb4r0C7VQEwQE66H8XfzE4bMNBs1Ja71xZi99DH=jL02_rpihnErl5S=mX4VO2158NwzcME3y1eD7BCKt=BsWb-eb=BFONCp3-dEDpj6fUFkbbiWCJb8jBC9SLzgA33j-wen37Y6fK0LastlkF=Q7MZz-BP0c6ymerHM3ynLBRvXVCcAZDM35aMr0JnVZF__c8XJ1oWeKfAkxqN2j9R-EqEBnqasNzkYaQ=XOBUH4t1D-b-4iqPkWFdF7SZ40HYmvydhX=kPOM7Om8OupMotf5uPOOGmEEyUFfz24EViR16j5=JOVl4vs6q0FwQfX6CfXfCl4k_TKs8HhN5-d8WPN0dq7n2y=rYBqwhY7JvVQHcq9zWu41uoudQMlOnBN7s9Gu7ChnfZUBrKHx3Mfsf_iNTBje4ECQ7O0KJSVujSnAenMyx8WkhvATUHMCLLU3=vZx7qF2irfJvBou=cbPGw0HRaVCk5uTpKP2cK2YxxmKvAxUEp17NebyReSAWcsCx7CpBuvx-rtqk3omDNydanD_sSumMnOBCf1t54Fu9dZFFT8uTuztJ72ClA7PidMmncC-lb9ttaUSZti-lJDWZ7-=tlykZVO5Nu1=mmEWLRQ2DqpHaRcDD43jiq=qDD453W0FYN26DoOfDvfAbzicpdiLNqbhMsc5GQ2-eC9O2c6EDQd93QkXmd3Zo4UxL7QKUY8M94krxPMcMCiQ4NWBt7AqUHvezRpCkkoZEP4-AgqrMGQpXfdkG4N2zcC5mKk4f-od2=sQcKaZpxXrxMLVUT2Wb=6qWL53fXH8MT-cqeb0XbNk90ViqUFaMiD=6rqqrJdDOnTXVdLs_fXmb9n27b6cHjuP8ei_tut-EHFuQ-LRL0=jT9YVBzW5M=KTW6oNtbfYGKxZpqon7wLs3wjsS--yJSOMacf2t=9S1Wk2afFh_vB5QV-HY1jZATRBPx=UvlPOg5nVumFuQM7Q4RmEnFo-aoSnozgscKWKXMfgcH_DmtcH7TQQcWAfPLHw8YnQgmfhP4Y6mVH98wKG84ss9sLNrxOCQtwxiH0KFO829UPMy1iqCqE0eKJPyaoGSBm6aRFZ8Yz5Kayr2y1fNgDRcJ4uqvc=pRFzpnqlZ2KmECOsPs=ugfmttKpg48QYg6dP=8KHB3ejtiXMPB4WQCZYmc8VGs_W8nENsVvjLzviQ3YgkW9Nh3ca-e683OnL5TFzSKoiM=0hCz==cWLn-UwiL_OquZ5ETFYnsOVHr3_66tzwTqdJOqov8fOgeFC=oEtMzMx46ZnnO7xpGu_ykc1UbueW=4QwHnvnfJpVktSN4YzXiaoDFcsQHLVj-Qpwh4Fr_rUm0E6ak8algthDsEy4C0XdekjKgBx8d8llOMH4cokuQU_Ye5tcXTxw1b_g2hs=Ce8oqcfSbmjePpTMQQXSNGTszgwTtgkzap-aK5xirdqgUAZwn14vYhL6o053w_bTfK0CqW0ef0usQar6in=3MhMtLEbgjtLfS0QU7qZl_auWks1mrRoSh6i0opWUGTVHluZEpq_956MZ7kN3Rh7e-ZcAKRhKn=c05SJf0ec21AlMLdJiEHrRaGSaC-AGu2dWNtp0Kq9iQKBbadMDaVPauQVkh9LS82S5WaQz_VYYH9ttaV7Vn3MrOqAwg8OXjGWTCr-uhMNO=egZK2qjjCOr6-AlYiWGHjJNgLsfgup5zj-kiSjmjCZ26mxVJvK-BEjHvqwKK20Sl-wqant6E2Tz0=D9Um7vwr-Ab6cll_kd3jr6B3f6ZF8HydZtuVBgoPEeriJDwGC=fmVx2uyXDBqJgrxkbLoShfb-uJ3OL=zi_3XSpeXWS7WAGLahxab6pYjBSjriEAUOPtrYofATstFcgvdQnlHhKmGtPTdRPv7YgozPt7FXQc0qrhsW2l=y=tVvQaGOEblWaSDEEaOvPDrORoZCv=0QW=qdm0fHB5tXcpFzxye7l1J3tuEvO-0_sVyDAnQXFw1gGUg_kSK3etWFT3A8uDiv-6CpeKZfLdUnWKS6jOqJ2VLT0CyOklFn93A-G3mPs8zrtuWfajR229TRSvfNu4iYB5CLcijHl1njh590t0xhw1tDdgSw8BP_g9F2DONPiooYnO9H7yM2ThM-JiQ41B2Wb62t8KKN6qoZgiVgr8fjWYA_tslpAWWHRkEuL4bZn7ud-pT1Z8soXLkYhVQa_TZuwuNSDW3b_q4uWcK=d18w9HLUgGZhRyBmg=Wzes0iFPXHkDOrqP7ecbYdBMRXeFuYfkoHDHxzp7ueX9749qDtP9ZU0z1hB7zCNhkEw5ZQ_rY42MMh7hXyZGcTQ88pdYhpxUCzLAH5=x9TvqbqUVatXKru0xyjlNbqn3n7ys7GS68He4hNYqSEsZcmcwMYja4tsBp7hNdYBJNQZ_CrV6ZbyQT-w3EvHGkVb6b5eCpkF-H6FlHOE=rWdnVzAheMJoj99aH1Tt98_fN4PEd1PB9OrrL_m1VahK9jYsLf66qFUV",
        }

        data = "user=alexandre.j.moore%40gmail.com&passwd=xfinity_Txzn3fr5%21&rm=1&r=comcast.net&selectAccount=false&s=oauth&deviceAuthn=false&continue=https%3A%2F%2Foauth.xfinity.com%2Foauth%2Fauthorize%3Fclient_id%3Dmy-account-web%26prompt%3Dlogin%26redirect_uri%3Dhttps%253A%252F%252Fcustomer.xfinity.com%252Foauth%252Fcallback%26response_type%3Dcode%26state%3Dhttps%253A%252F%252Fcustomer.xfinity.com%252F%2523%252F%26response%3D1&ipAddrAuthn=false&forceAuthn=1&lang=en&passive=false&client_id=my-account-web&reqId=efb11ffb-b5c1-4e32-b4ce-6de3b53145e4&X-hzfdeCEGvt-f=A8lYmIp0AQAA19gju66AaW7xJiFhi77JtNM5EB2bMT2s57qtu9WEVUtueKLpAJy4FKHAfwAAHvUAAAAA&X-hzfdeCEGvt-b=-3dlcvj&X-hzfdeCEGvt-c=A6oSlIp0AQAA43k9y2GosD_5efxfTTyXR50AO4_iypBfswMUYzq20QDAIYhLAOGmu1bAfyxHMl3su0Lq&X-hzfdeCEGvt-d=o_0&X-hzfdeCEGvt-z=p&X-hzfdeCEGvt-a=aj7H_YqBQyQxVR_q5yTmoiVruj87UTi91MLCvgW1Jr1o5G_NZun2TEKsj2ae%3DMWEQRSPmw_NBlgBxqxLvbAu7JM2Pa52OdI4LWq9h2keCfKQ76CT0lyHbmr1mOwqvfITWYeg2x_v%3DywX7ESsd_JYxJoImO1MVBhPA54aR9DB%3DWyAtwsPmTW_vY0Kf4G2TVI2%3DEZCRYHJnD4lI-vYEWqsABaTNcDC9wiA55sE9O1AaLN40tZCAkMBH0SeG6SZEADTsZ77WZPcLBjrz-vvqb1qmm3KS3PnxcqouJXLbqqbHIcZPsUA8q_WXzXJ82hehUB3niHsmyjDwz0SDhZzsAZI0NUr7osv52M2DI0qhHvSNQwar%3DfZDacVX36qo7GQZCoEW_Yc09pi3ijR2n518Kwp03cNlhEHbd1hM0IE68zh2fam%3D7s6mNV_wzreeQE3eGzHzwnhvj9uKVsHIKuajya9OqJ5Nj0EJVdCx%3DoDSCGirXIN7eETxudZEPhM3gJ4gdohUtoftG5gU_yvWcxq1%3Dgm5yiqUmHs3HUxIOY6kB7n7B9CQBkkOPIxUWcpbje7Z5ph9TuISCCss3Um2hr45PpOYMXAp-qi1avMqEkus5_sIymipJoN6BN6KvtvAxb7zS8j6WDwPwtn7wJeKHnkBgLu-%3DyCBmc-wZc2O2xc8bViWBmI32AEN6BLpC_JwQvTAQrR8m0sM7yTh4pQN2uaQ-uW%3Dx%3DkQt3n6flfPnmSTtTiwbRbzttRkSl_XmXGMEeYd8mR6IRm89rScDoiL25IjtM-kCkUKWR5c_l9NC1EsrnJWrz0VUTrgRDt9eALE%3DQ%3DesCjCIjKJwGoTOMGIft7kxAxv5L6demqSnXSR_kZ0DOjBzE1aiK5iJ7_Y9JvNYPZXwZ5LymisROuC1K1A5qDXbWm25XzPuBdbVAS_dTZVh%3DQ67I4x99ivUUm6io-9T4GuJ3XvW0vJDl%3DcP6cGIaCQYBlEKZJwx_9aVnPmRe82GtI7XEl2Cd35Wo1uGGNncxsvzo945xnqJl0qYCfJCum0xI-575eIh0WPDKq-nRnzPyLtd-3g2za64IOzWQPao7q325OGP63oza%3DSntBMwIJaREX9%3DgCS5vQ4x_ep%3DG6qObxYGuknoyLgpJmw6A9cCay4PsDfj%3DT%3DhrsQuDarnWlNY3N_up0B63%3Dz2Q0O7m6i_aJxRAG8l5_Zv2hIMvwMQehlS6QMfCUgI2PLo%3D%3DdWW4N3aap9bS-yxN85eRBIgs1uxXGJwBQfgasrXs6BQZa77GdRmTBWaCeWDQIGJ%3Dv0jic6GMy6mlqbVopkmbrW8u3YoxaSIeEbV8ANH1YbzY3XO9skcRmMKKINYAqd0dfV67BQwxgPmp%3D0-5VnjBY30TRoIUqy1DuWjYbTWqWT%3Dmssgw%3D7xP2cxu1KeDCNA5tZkdlvayGYMQoTU1X0xWr3zWc_B4twOJ5mOV585ay_cs2k60KzjAjRf4_VXt_syIGiCpa2zmDpRjwtX6Jbp87mRB-QuXROVzzvU0pRDIYg8WH1Z2rExt-soxu-w_t6p4u60oi4v8eGI93lpAIjnpkyY43Tzjn7fp3-RGe5UJtpqaZawHE-bp8AshVqj58lPGi%3DCbPvWBoadlxUu3wQednz5wIBX0MKTyuteJHqP9f0p7ZsK95ZncvyyBmvlcPEJfQjKAyDbfW6o93n23uz5WijNDmCiW6BeN8czcBvB4PYGfJLoPZuPMP1qesgE41nyeEQ7eltzkmA3%3DnoAZ_y-gKsuSXjkOM-nfsc1Gzeg2Q8EUB4s5Cn2z%3DpY2EaTtIKeovXwQjTE32l3gPLOc1%3D0Uo5am7esqb1-QGqZLOBRB8Rs%3DP9VWJa9LwgsRnqiXt346IAvs9su0DUsZN6MzesEvz-VPZIMuISO0h8gZCif0JlgC3Y6SD4KbgK55mk128piisnsfkQ3KbqbDixawCOuOQschQbLQCfU0Kbzmlw6_Jid_ZSQNxL946T-l-SK2Hyg8bhBUsyUPLgwzChkC04WdaG0ffXTdvbcxMzQqvW3KSgeU3tPS%3DG_JmaklD%3DC4HbX1TzjVY3A71nc5UIo10QGl0dCj2A4HAgZRRQuCeEbLJfav7PPfxuVMC1I%3DrMj54DK4hMlGqKMoV8ZLRV1-y0JDAcG9948bk4f8Be4G8M_Azki9ozlLS0Mwbr8mjiSWxlaLrcgh0WrE_jYZKKYzRgppYLd2vwvTdXOT0PaWgw-R4DSfCxOVdzxuXZXguKwhH21mP6otsMv4gCD6Kd_-v09vCuIYXwgJmRnkcSwbEsq9GMLAaAciUQjzMYxtId6tmsg8qtjkJWRoLil-yNZ8YcBJnhaHwo2lt8VJ8ghkd_v9G522ciBwiP7MmG26LLZML-15bR6Klybn7mqS3pAAb2o6J27z8UhyhM1%3D6ENoCEbkvIab_BqoayDCfVCRJnSMusZrn5gtsx05e0h%3DihwGSY-dueeDl8y2OlPf80JRoT2k-BVUAb6ycD3ueCjRgzUqMDlotYVz-xwR7sQJG75BQsKA8Iaeu2i3oIdhTEW5BGODi2aVPZ_zfIcWX-Ah6-t4CphVslx%3D_pJcylY1DDINdOv_NHcaJTS0H-aVop9E9cHg7BQZOA72Tpn_2tsBGZdcJy5uKkKsJ2QZS29aKBu%3D28ZKs7ovllxzMKjSWc9qAaklflO543_AJlvvhqOq0TPcPamMIVu6j-7JYLn1E-JGlyk2MM7vL5L_f7KTEwiTtIh4QmeLbMEhpMNa3qRHkJ4w_XnDpTj5tXoM6Z6ubVWiAoergeVRWK0yPJU_9XXtxaWR4yVCMqTlcj1%3D1lu-ncGmYR-0UkdO4wMRDqsdSRbTUhTAHMEzT%3DSSIzMnn93AwAdsbgG4r5kyTeSdhyAoAgVEimE_Jne1DUCjgJ0SXoB76qib1jWqnhRT6RN-rYgxy-a0bWj0K_h0%3DHGpk1jXvkdYr0JwKDMxdYYRTm%3DY3x5MAnZXO5S2zdeq1u1j9PbQBXL3-3z0d%3DMtsZpuoemhhgONQ5quv8u7xp0fhI8Jpm6qMvC%3DgDA5k%3DPr8tkcSvvjA58YSBJfJceGIpT9UAh3qm3fv%3D4Lgd6zAuI1KSbitIdDKeU82SrKJe7Etzrtq2uMumdl4%3D1fohjNj0k_qjw01yb0raTJsrutkHqRv%3D0JrSbfqCZNbQad%3Dij-q8zn7qWMCxI84XnQ4J4HNK%3DROyZosLS8n3k7l8qIU5ux-04T0t1gokhO71AnsstO4pDRIm%3D47%3DvsyuZOBizywPe%3DqaKT_i7LXpmGVL0koaHe9tb3ypAqfGOC-H6lYEEg-hp7mjQsZnNDt%3DGtp3StfS4xz13w7993uR1gZnS4qt_AhDLrvd_KVbe44O7DvrOAHrr-IIZ-u_bMqJKTxgpIBb123B110aWEJz-0rp8IQ5mOPuC7s2g_nyc6SEWj-Co-003_XXK8x8oxzt-9RGp5wCOsq9NdHYV0Ecb_29dv5GSGzNB8pL0STtQN8hEhD0DV5HyzOAsahJVap7t_5MqObNM%3DL-Ur_XRWhOM5SOxN2kD9XWGSG3a6CgLP3_LDy7UlPYK8gLYmm6R-b3ONgBVSaDVG_6mRojqqujWQcdydxgeaX7z7pN64DIm-Lr4mcu3AzK9_ekIalgUlk5k9KZKDxw1sYN976xDH1H88mk5YbfBcER3kxm9BoELgcoe2vhtED1met6c7H1%3DG7c-M7v1sbggHaStoO4k6js0i0h1PAXuACT4Lwxx-v5klYjG3-CIcQyIxhJmQs8LV4-od_CJV73c8l4tA3_17TaabmCD24QH87tkORYqt_Czi_A4HLh%3DIjCyOMsMKXkcIjDSTB92JKXWn%3DuS5HhNzUaCUc9ysXe1%3DNZAopf9CwzdR6LrDQQQlh8tku8lhhTtgyiZkm2qn-n3tWW2ytJrKz3ohVkngOYADErJAwLR2AmQZ2xBPzH2KCCqAZXN9Ak2gCx0jZt1bjbAsMp82NCiyVvm95GN-tB_i%3DojkG0bkOKdDMwS2Lv9%3Dr%3D03asznsLtTxBS5KA_0wRUqJOpv"
        params = logger.debug(urllib.parse.urlencode(params))
        # data = urllib.parse.urlencode(params)
        res = self.session.post(URL_LOGIN, data=data)

        if self._is_security_check(res):
            logger.warning("Security check found! Please bypass online and try this again.")
            return

        # logger.debug(res.content)
        # if res.status_code == 200:
        #     logger.info("Login sucessful")
        # else:
        #     logger.info("Login failed")

    def _format_output(self, js):
        return [
            {
                "measurement": "xfinity",
                "fields": {
                    "homeUsage": js["usageMonths"][-1]["homeUsage"],
                    "allowableUsage": js["usageMonths"][-1]["allowableUsage"],
                    "unitOfMeasure": js["usageMonths"][-1]["unitOfMeasure"],
                    "courtesyUsed": js["courtesyUsed"],
                    "courtesyRemaining": js["courtesyRemaining"],
                    "courtesyAllowed": js["courtesyAllowed"],
                },
            },
        ]

    def run(self):
        for attempt_number in range(2):
            logger.info("Fetching internet usage...")
            res = self.session.get(URL_USAGE)
            logger.debug(f"result - {res.status_code} {res.content}")
            if res.status_code == 401:
                logger.info("Session is not authorized, attempting to login")
                self._login()
                continue
            if res.status_code == 200:
                logger.debug(self._format_output(json.loads(res.text)))
                self.output(self._format_output(json.loads(res.text)))
