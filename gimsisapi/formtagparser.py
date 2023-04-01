import re
from typing import List

from bs4 import BeautifulSoup

from constants import AbsenceType


def get_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    m = {}
    for i in soup.find_all("input", type="hidden"):
        m[i.attrs["name"]] = i.attrs["value"]
    return m


class GimSisUra:
    def __init__(self, ura, dan, ime, kratko_ime, razred, profesor, ucilnica, dnevniski_zapis, vpisano_nadomescanje):
        self.ura = ura
        self.dan = dan
        self.ime = ime
        self.kratko_ime = kratko_ime
        self.razred = razred
        self.profesor = profesor
        self.ucilnica = ucilnica
        self.dnevniski_zapis = dnevniski_zapis
        self.vpisano_nadomescanje = vpisano_nadomescanje

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"GimSisUra({self.ura}, {self.dan}, {self.ime}, {self.kratko_ime}, {self.razred}, {self.profesor}, {self.ucilnica}, {self.dnevniski_zapis}, {self.vpisano_nadomescanje})"


class SubjectAbsence:
    def __init__(self, predmet, ni_obdelano: int, opraviceno: int, neopraviceno: int, ne_steje: int, skupaj: int):
        self.predmet = predmet
        self.ni_obdelano = ni_obdelano
        self.opraviceno = opraviceno
        self.neopraviceno = neopraviceno
        self.ne_steje = ne_steje
        self.skupaj = skupaj

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"SubjectAbsence({self.predmet}, {self.ni_obdelano}, {self.opraviceno}, {self.neopraviceno}, {self.ne_steje}, {self.skupaj})"


class SubjectAbsenceStatus:
    def __init__(self, ura: int, predmet: str, napovedano: bool, status: str, opomba: str):
        self.ura = ura
        self.predmet = predmet
        self.napovedano = napovedano
        self.status = status
        self.opomba = opomba

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"SubjectAbsenceStatus({self.ura}, {self.predmet}, {self.napovedano}, {self.status}, {self.opomba})"


class Grading:
    def __init__(self, datum: str, predmet: str, opis: str):
        self.datum = datum
        self.predmet = predmet
        self.opis = opis

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Grading({self.datum}, {self.predmet}, {self.opis})"


class Grade:
    def __init__(self, ocena: str, datum: str, ucitelj: str, predmet: str, tip: str, opis_ocenjevanja: str, rok: str, je_zakljucena: bool):
        self.ocena = ocena
        self.datum = datum
        self.ucitelj = ucitelj
        self.predmet = predmet
        self.tip = tip
        self.opis_ocenjevanja = opis_ocenjevanja
        self.rok = rok
        self.je_zakljucena = je_zakljucena

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Grade({self.datum}, {self.ucitelj}, {self.predmet}, {self.tip}, {self.opis_ocenjevanja}, {self.rok}, {self.je_zakljucena}, {self.ocena})"


def get_class(text):
    soup = BeautifulSoup(text, "html.parser")
    m = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}}
    for i in soup.find_all(id=re.compile("ctl00_ContentPlaceHolder1_wkgDnevnik_btnCell_.*")):
        parent_classes = i.parent.attrs["class"]
        dnevniski_zapis = "dzObstaja" in parent_classes
        vpisano_nadomescanje = "flagS" in parent_classes

        kratko_ime = i.find("b").text
        id = i.attrs["id"].split("_")
        ura = int(id[4])
        dan = int(id[5])

        title = i.attrs["title"].split("\n")
        ime = title[1]
        razred = title[2]
        profesor = title[3]
        ucilnica = title[4]

        m[dan][ura] = GimSisUra(ura, dan, ime, kratko_ime, razred, profesor, ucilnica, dnevniski_zapis, vpisano_nadomescanje)

    return m


def get_days(text):
    soup = BeautifulSoup(text, "html.parser")
    days = []
    for i in soup.find_all("th"):
        f = i.find("span")
        if not f:
            continue
        t = f.text
        if re.match(r".*, .*", t):
            days.append(f.text.split(" ")[1])
    return days


def get_absences(text, type: int):
    soup = BeautifulSoup(text, "html.parser")
    absences = []
    if type == AbsenceType.by_subjects:
        for i in soup.find("table", id="ctl00_ContentPlaceHolder1_gvwPregledIzostankovPredmeti").find("tbody").find_all("tr"):
            f = i.find_all("td")
            absences.append(
                SubjectAbsence(
                    f[0].text.strip(),
                    int(0 if f[1].text.strip() == "" else f[1].text.strip()),
                    int(0 if f[2].text.strip() == "" else f[2].text.strip()),
                    int(0 if f[3].text.strip() == "" else f[3].text.strip()),
                    int(0 if f[4].text.strip() == "" else f[4].text.strip()),
                    int(0 if f[5].text.strip() == "" else f[5].text.strip()),
                ),
            )
        return absences
    elif type == AbsenceType.by_days:
        current_day = ""
        days = {}
        for i in soup.find("table", id="ctl00_ContentPlaceHolder1_gvwPregledIzostankov").find("tbody").find_all("tr"):
            f = i.find_all("td")
            if re.match(r"(.*)\.(.*)\.(.*)", f[0].text.strip()) is not None:
                current_day = f[0].text.strip()
                days[current_day] = []
                f = f[1:]
            
            days[current_day].append(
                SubjectAbsenceStatus(
                    int(f[0].text.strip()),
                    f[1].text.strip(),
                    f[2].text.strip(),
                    f[3].find("div").text.strip(),
                    f[4].text.strip(),
                ),
            )
        return days
    raise Exception("Unimplemented")


def get_gradings(text):
    soup = BeautifulSoup(text, "html.parser")
    gradings = []
    table = soup.find("table", id="ctl00_ContentPlaceHolder1_gvwUcenecIzpiti")
    if table is None:
        return gradings
    for i in table.find("tbody").find_all("tr"):
        f = i.find_all("td")
        gradings.append(
            Grading(
                f[0].text.strip(),
                f[1].contents[1].text.strip(),
                f[1].contents[2].text.strip(),
            ),
        )
    return gradings


def get_grades(text):
    soup = BeautifulSoup(text, "html.parser")
    gradings = {"subjects": [], "average": 0.0}
    table = soup.find("table", {"class": "tabelaUrnik"})
    if not table:
        return {}
    all_grades = 0.0
    all_grades_count = 0
    for i in table.find("tbody").find_all("tr"):
        subject = i.find("th")
        f = i.find_all("td")
        subject_grades = {
            "name": subject.find("b").text.strip(),
            "average": 0.0,
            "perm_average": 0.0,
            0: {"average": 0.0, "perm_average": 0.0, "grades": []},
            1: {"average": 0.0, "perm_average": 0.0, "grades": []},
            2: {"average": 0.0, "perm_average": 0.0, "grades": []},
            3: {"average": 0.0, "perm_average": 0.0, "grades": []},
        }
        total_all = 0
        total_all_perm = 0
        total_all_perm_count = 0
        for k, n in enumerate(f):
            total = 0
            total_perm = 0
            total_perm_count = 0
            total_len = 0
            for g in n.find_all("div"):
                useableGrades = []
                grades = g.find("span").find("span").find_all("span")
                previousTitle = ""
                for grade in grades:
                        title = grade["title"].strip().splitlines()
                        datum = title[0].replace("Ocena: ", "").strip()
                        ucitelj = title[1].replace("Učitelj: ", "").strip()
                        predmet = title[2].replace("Predmet: ", "").strip()
                        ocenjevanje = title[3].replace("Ocenjevanje: ", "").strip()
                        g = grade.text.strip()
                        vrsta = title[4].replace("Vrsta: ", "").strip()
                        rok = title[5].replace("Rok: ", "").strip()
                        stalna = "ocVmesna" not in grade["class"]
                        subject_grades[k]["grades"].append(
                            Grade(
                                g,
                                datum,
                                ucitelj,
                                predmet,
                                ocenjevanje,
                                vrsta,
                                rok,
                                stalna,
                            ),
                        )
                        if ocenjevanje != previousTitle:
                            useableGrades.append(grade)
                            total += int(g)
                            total_len += 1
                            if stalna:
                                total_perm += int(g)
                                total_all_perm_count += 1
                        previousTitle = ocenjevanje
            if total_len != 0:
                subject_grades[k]["average"] = total/total_len
            if total_perm_count != 0:
                subject_grades[k]["perm_average"] = total_perm/total_perm_count
            total_all += total
            total_all_perm += total_perm
            total_all_perm_count += total_perm_count
        full_total_len = len(subject_grades[0]["grades"]) + len(subject_grades[1]["grades"]) + len(subject_grades[2]["grades"]) + len(subject_grades[3]["grades"])
        if full_total_len != 0:
            subject_grades["average"] = total_all/full_total_len
        if total_all_perm_count != 0:
            subject_grades["perm_average"] = total_all_perm/total_all_perm_count
            all_grades += subject_grades["perm_average"]
            all_grades_count += 1
        gradings["subjects"].append(subject_grades)
    if all_grades_count != 0:
        gradings["average"] = all_grades / all_grades_count
    return gradings
get = """
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" dir="ltr" lang="sl-SI">
<head id="ctl00_headGSE"><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /><title>
	Ocene učenca
</title>
<link rel="shortcut icon" href="../../App_Themes/Images/favicon.ico" type="image/x-icon" /><link href="/App_Scripts/jquery/css/base/jQueryBaseCombined.css" rel="stylesheet" type="text/css" /><link href="/App_Themes/Css/GimSisCombined.css" rel="stylesheet" type="text/css" /><script src="/jQueryCombined-5ea9fef0-c516-498f-8150-585cc5ccd1a1.js" type="text/javascript"></script><script src="/GimSisCombined-588a62fd-7435-4c5c-98fc-12967dcdf999.js" type="text/javascript"></script>
    

  <script type="text/javascript">
    jQuery.getRootUrl = function (path) {
      return '/' + path;
    };

    function userTitleBlink() {
      var oObj = $("#divMasterUserTitle");
      oObj
        .animate({ color: "#ff0000" }, 1000)
        .animate({ color: "#ffffff" }, 1000);

      var oObjInner = $("[id$=divMasterUserInner]");
      oObjInner
        .animate({ borderColor: "#ff0000", borderWidth: "4px" }, 1000)
        .animate({ borderColor: "#ffffff", borderWidth: "4px" }, 1000);

      oObj.queue(function (n) { userTitleBlink(); n(); })
    }

    function setupUserTitleBlink() {
      var sExecute = $("[id$=hfUserAlert]").val();

      if (sExecute == "true") {
        userTitleBlink();
      }
    }

    document.showHelpId = "GSE";

    function printEl(aElementSelector) {
      gssPrintElement(aElementSelector,
        [
          '/App_Scripts/jquery/css/base/jQueryBaseCombined.css',
          '/App_Themes/Css/GimSisCombined.css'
        ]);
    }

    function DownloadFile(aId) {
      gssCanSelectRow = false;
      var sFileLink = '/Page_Handlers/FileDownloadHandler.ashx' + '?FileId=' + aId;
      window.location.href = sFileLink;
    }

    $(document).ready(function () {
      closeModalWindow = false;
      parent.$.fancybox.doPostback = false;

      var prm = Sys.WebForms.PageRequestManager.getInstance();
      prm.add_beginRequest(MasterSaveScrollPosition);
      prm.add_endRequest(MasterRestoreScrollPosition);

      prm.add_initializeRequest(saveDivScrollPosition);
      prm.add_endRequest(restoreDivScrollPosition);

      prm.add_endRequest(MasterHighlightMenuPath);
      prm.add_endRequest(setupUserTitleBlink);
      prm.add_endRequest(displayServerError);
      prm.add_endRequest(MasterBeforeExecute);
      prm.add_pageLoaded(MasterNormalizeEdits);

      MasterBeforeExecute();
      setupUserTitleBlink();
      MasterHighlightMenuPath();
      checkServerHFError();

      WriteDateTime("divFooterLeft");
    });

    function MasterBeforeExecute(sender, args) {
      if (__This.isIE === true) {
        $("a.csbuttonmodern").bind({
          mousedown: function () {
            if (!$(this).is(':disabled') && !$(this).is('[disabled]')) {
              $(this).addClass('br-ie');
            }
          },
          mouseleave: function () {
            $(this).removeClass('br-ie');
          },
          mouseup: function () {
            $(this).removeClass('br-ie');
          }
        });
      }
    }

    function MasterNormalizeEdits(sender, args) {
      if (navigator.userAgent.toLowerCase().indexOf("chrome") >= 0) {
        $('input:-webkit-autofill').each(function () {
          $(this).val("");
          $(this).after(this.outerHTML).remove();
        });
      }
    }

    function formatError(message, errPrefixes) {
      if (message && errPrefixes && errPrefixes.length > 0) {
        for (var i = 0; i < errPrefixes.length; i++) {
          var errPre = errPrefixes[i];
          var errPreLen = errPre.length;
          var errPos = message.indexOf(errPre);
          if (errPos >= 0) {
            message = message.substr(errPos + errPreLen).trim();
          }
        }
      }

      return message;
    }

    function displayServerError(sender, args) {
      if (args.get_error() != undefined) {
        var oError = args.get_error();
        var bDisplayError = __This.DisplayAllErrors && oError.httpStatusCode != 0;
        //var sErrorMessage = oError.message;
        //var iGSErrPos = sErrorMessage.indexOf("GSERR:");
        //if (iGSErrPos >= 0) {
        //  bDisplayError = true;
        //  sErrorMessage = sErrorMessage.substr(iGSErrPos + 6).trim();
        //}

        var sErrorMessage = formatError(oError.message, ["GSERR:", "Sys.WebForms.PageRequestManagerServerErrorException:"]);

        __This.IsLastRequestError = true;
        __This.LastRequestErrorMsg = sErrorMessage;

        if (bDisplayError) {
          args.set_errorHandled(true);
          tbError({
            title: "Napaka",
            innerHTML: sErrorMessage.replaceNlWithBr()
          });
        }
      }
      else {
        __This.IsLastRequestError = false;
        __This.LastRequestErrorMsg = "";
      }
    }

    function checkServerHFError() {
      var ohfError = $('[id$=hfError]');
      var sErrorMessage = ohfError.val();
      if (objIsFull(sErrorMessage)) {
        closeModalWindow = false;
        if (parent && parent.$.fancybox) {
          parent.$.fancybox.doPostback = false;
        }
        ohfError.val(undefined);

        //var iGSErrPos = sErrorMessage.indexOf("GSERR:");
        //if (iGSErrPos >= 0) {
        //  sErrorMessage = sErrorMessage.substr(iGSErrPos + 6).trim();
        //}

        sErrorMessage = formatError(sErrorMessage, ["GSERR:", "Sys.WebForms.PageRequestManagerServerErrorException:"]);

        tbError({
          title: "Napaka",
          innerHTML: sErrorMessage.replaceNlWithBr()
        });
      }
      else if (__This.IsLastRequestError) {
        closeModalWindow = false;
        if (parent && parent.$.fancybox) {
          parent.$.fancybox.doPostback = false;
        }
      }
    }

    function MasterSaveScrollPosition(sender, args) {
      var oBody = $("[id$=MasterBody]").get(0);
      __This.SavePagePosXMaster = oBody.scrollLeft;
      __This.SavePagePosYMaster = oBody.scrollTop;
    }

    function MasterRestoreScrollPosition(sender, args) {
      var oBody = $("[id$=MasterBody]").get(0);
      oBody.scrollLeft = __This.SavePagePosXMaster;
      oBody.scrollTop = __This.SavePagePosYMaster;
    }

    function MasterHighlightMenuPath(sender, args) {
      // $("div.horzMenuEx ul li").show(0);

      var oObj = $("div.horzMenuEx a.selected");

      if (objIsAssigned(oObj)) {
        var oEl = oObj.get(0);

        if (objIsAssigned(oEl)) {
          oEl = oEl.parentElement;
          if (objIsAssigned(oEl)) {
            oEl = oEl.parentElement;
          }

          while (objIsAssigned(oEl)) {
            if (oEl.tagName.toLowerCase() == 'li') {
              for (var i = 0; i < oEl.childNodes.length; i++) {
                var oSubEl = oEl.childNodes[i];
                if (objIsAssigned(oSubEl) && objIsAssigned(oSubEl.tagName) && oSubEl.tagName.toLowerCase() == 'a') {
                  addClass(oSubEl, 'selected');
                  break;
                }
              }
            }
            oEl = oEl.parentElement;
          }
        }
      }
    }

  </script>
  
  <script type="text/javascript">
    // zaradi updatepanela in postbackov je potrebno ujeti konec vsakega requesta in tam povezati vso jQuery kodo!!!
    $(document).ready(function () {
      var pgRegMgr = Sys.WebForms.PageRequestManager.getInstance();
      pgRegMgr.add_endRequest(afterAsyncPostBack);
      pgRegMgr.add_endRequest(excuteAfterLoad)

      excuteAfterLoad();
    });

    var tabSelectedSQLExplorer = 0;

    function excuteAfterLoad() {
      setupModalBox("Komentar za poročilo (Student's self assessment)", "#btnVnosKomentar", "[id$=btnRefresh]", 'iframe', 'no', 500, 200);

      $("#tabs").tabs({
        select: function (event, ui) {
          // var $tabs = $('#tabs').tabs();
          // var selected = $tabs.tabs('option', 'selected');
          var tabSelected = ui.index;
          // shrani zadnjo izbrano stran!
          $.Storage.set("tabSelectedUcenecOcene", tabSelected.toString());
        }
      });

      // postavi se na zadnje izbrani tab
      var $tabs = $('#tabs').tabs(); // first tab selected

      // poišči vrednost parametra v lokalni shrambi
      var tabSelected = $.Storage.get("tabSelectedUcenecOcene");
      $tabs.tabs('select', parseInt(tabSelected, 10));
    }

    function afterAsyncPostBack() {
      // odblokiraj stran, če je potrebno
      unblockPage();
      return true;
    }

    function vnosKomentar(aIdPredmetKrovni, aIdOcObdobje) {
      $("#btnVnosKomentar").fancybox.hrefParams = Base64Ex.encodeURL("Id=" + 'mark.marjanovic' + "|Type=|IdPredmetKrovni=" + aIdPredmetKrovni + "|IdOcObdobje=" + aIdOcObdobje);
      $("#btnVnosKomentar").click();
    }


  </script>
<style type="text/css">
	/* <![CDATA[ */
	#ctl00_menMain img.icon { border-style:none;vertical-align:middle; }
	#ctl00_menMain img.separator { border-style:none;display:block; }
	#ctl00_menMain img.horizontal-separator { border-style:none;vertical-align:middle; }
	#ctl00_menMain ul { list-style:none;margin:0;padding:0;width:auto; }
	#ctl00_menMain ul.dynamic { z-index:1; }
	#ctl00_menMain a { text-decoration:none;white-space:nowrap;display:block; }
	#ctl00_menMain a.static { text-decoration:none;border-style:none;padding-left:0.15em;padding-right:0.15em; }
	#ctl00_menMain a.popout { background-image:url("/WebResource.axd?d=pSmkg-AL9RxxxpL_7StQYQ2t9IXHbC4NZlIwNgYjF1Q-fPxEgFcMgEoSml2Ub7bCKKfJveCL-oSKOPYExYnp5hAP_9R9EiX9OLDdms0klrE1&t=637811765229275428");background-repeat:no-repeat;background-position:right center;padding-right:14px; }
	#ctl00_menMain a.dynamic { text-decoration:none;border-style:none; }
	#ctl00_menMain a.static.selected { text-decoration:none;border-style:none; }
	#ctl00_menMain a.dynamic.selected { text-decoration:none;border-style:none; }
	/* ]]> */
</style><meta name="keywords" content="SC" /></head>
<body id="ctl00_MasterBody">
  
  <form name="aspnetForm" method="post" action="./OceneUcenec.aspx" id="aspnetForm" enctype="multipart/form-data">
<div>
<input type="hidden" name="ctl00_ScriptManagerMaster_HiddenField" id="ctl00_ScriptManagerMaster_HiddenField" value="" />
<input type="hidden" name="__EVENTTARGET" id="__EVENTTARGET" value="" />
<input type="hidden" name="__EVENTARGUMENT" id="__EVENTARGUMENT" value="" />
<input type="hidden" name="__LASTFOCUS" id="__LASTFOCUS" value="" />
<input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="j/PCZzYLdozx0kUgWVTp22ZFYuXzohMbe+02v9PW3/VWQYVyH/5kPqJKlsSPOS46w1FlXYErMRKA6wlI1Bk188EnfLAsQcahRzKW2j8+kO8XS/BgJPiQdr9r1PIe6W31FT6vlVXcDnJ+bhkdORHfUwZ+2uPDXfUvmC6TUfkhx8jHhODALpcOaQs15/TBqz9sMnw89ThzQlyGGjgc+UfiwqFUY1U+9MHOeECphD3vPXpj0E6qIpSnLXZ5974UKzLk9fpZoddIrS508NNo8FuvSas4dsjKAWfH6qpmsaWr3D+2ymcX9IgFi8Pw4UzRm6MbMvM/T/2nBQJpzvQ108HXRpdjalS8Wd4WJw9gPrwIbDrXrKktWurzX8hJHzGsBtgDCLD140+lCSdCrvLJK1KWeAJpl4rYXG5aRURfylm8WA5TG/nw5+IOs7WtDWkcMX/Ln4zP61b26lmXo3to5UcMzxZ0SxlDgeAZJGuXXWeHGzXF5gBMiK15NhRWLvOaNj4aHOzmBuzdLotXTT+KxIcd26bKSANidCaHpwJC1n4j3XebLfyijfnnf8wftObSWzLAGZtxf/wzn+5z/Yd9T+YJVV/LxUfKfy36y7oFYiaxyfKmPAdZSHM9wOCO6pUklyYsb6Vsp48oS3flROu2aw0gGHWgSan1bYOVSMXVyaPTN/K2ldcxC1pGVXqSXLi0mP+F4c4mqsyQwlbSeyT9Y+EtZsF1pM/EeFW6uE81VWu/3zGft4aD/bE91Dh9o5fn7WHdjyX0eIGBvuTbH8Y04T98lz/DHFAkyi8jIdkAvfXD7Fu+Tm7a4rI+S26k7EmVIUks61iIqexNZHI9l20KH/aky6CDMJmKiL8UzBujwwFwz+vGfJ7HWmepl0bNq97+5LeET9guK4JnR7OORsM6xbbdIn2W52zJR6/v2f1Sn7xbFWZ8gJP6GkSXKrsQQ1Yc+YLbeSl0NnewjWHJq9yO10wZLOVYAoC/eMmxpin/8yYXwEOwZwDYDooAJR1fhg+qbIuRySI/tS6Lm6GrjMj2UJyAxF3MUgITyviI/aIYdtFuyFHTBNpB9trq0RgAu48h0Os2fiOej6be29LJlv0v49wfMSYhfhgXDJTD1HnZy7ZFAc88ddGEgzwOZZpXNBEoLsMDOJzWzaBn89oJtNUp2Xfwo32mkK1tZiEahT3iQdMNPbY8vN882LVISMGhK1yLkxHPD/wPhNDEHUYj5UQAUHu0iafZX2rXQrPqryJp7eK5k+xO3NuFk69IyYQO6AQ4T+KVkEL4FFVU7+wOAzMMVJhpvG9rXu5mmHUHTQVtJxTbZPpYOw83YFT01gjd8r3NEMozC9vAc5kT6l7Ohy3+G2Np41jNfQxLK/AbVETOb7su5dhkmvfXCwoe13l0U7FqNbr/JtBq1OKxyPgIovqe79bqg9STvgqEvxcrGf8uj2aY7eVeYCXieVebMGAfXCcYjPhHjwTUB81bW+Y92cb0ApxFQCoETddiXH2mUShyBTqGVqz+HTi8XJhHqMCvnwInb4z1NcbBnrzyosJfDZlETo0KAEBJB84d8AgXEhqjUreTwMvkRuV6QJ2rh78pmI9C3AGNd8UT3nG/sraGS1usPkk1rFUAUK4MBOWJwMUWbitzDdypQU/3MIA/C1kMt69Trwl6gvEwUi8IjrmOZUQLlpUmMsNDAwgJ4My59QV07QK334BKG6kJd77lw5roMb2B30F9ubnr32xlE2fjSLPhZ5lqx9ZL+hX7dPaBuGBSlC+3RiPWo3QPTpdXEozPGOnUwYTQ4hNzCJVLoDC1uy5wNXZewAt6XDeatSwlP88snZlAQKC7HOU2r6aYuPUqenuLqCy3m/NWKIEr1uedVwC4tjp8hVFC8xsU7oaURxg6y9RutwQC1n0blpEdpAIWa+otxS8IJtdyO7oepzCdci5ut6XTv1LmxsAplGbENpqQIJZ1wJZa9/86ODso0gBihYqi9Pstyj3nn0OunPTOr3r3+630bpk+Cc4R35kqwJuSHMBixC+WMPKN0/xYaY7e1KJEp/KhmWrKRHXKjGDB06+XPZXxzP73z7ssHSgtTA6i2uK6XZyBfBgWfEp7zWuomcME17xIgVfE/koqo4b5G+X/HMl5HCiT4gMqEgsuUf6PApTuNvEcb/AXa33rB8NVS/hF8RnyLa6gQIoH64Z1F83EWaBzqoB90AmXnotgSY1cpf2VgLi8ByY3ua+ZCkGKAUfhNOk2LIfqi7GPO1zK609GZh/U4F+ByZtdxvEeU+OSa/DeSAQR70BYwbci2O9ESUfhpMednMjOC/6s3gDQGx2wDI66kHzLa8+YjCEAe3OdF2UevBjzpNZQuJQ3Q00fslmYPZawoateoXBffFSeAJLwQWWq3+LTKjiYIIVJHHDO01VlAFEWqNlhTSri48wjKiMHKKHafIbRPK/EC3Q5mDqHwt0cEZFZOtntlvlQy3g6WCCkDi6ltRGOLa4xg46hQdltq+3R71DEL8iOgeSJb9xL9PXN8GDgG6XMqn/tnBkCaGeh5eynunCnmJT1Z59nqelk+ZvjSr+OFiQWoxR19gotzQ1ffjeYjdpQ/71tPUcRHXJelMv5MJHke3Jbv095/bwfdFgZbUKdGP0NgsmtqPlYBbZ7qHlnx5OjRF2O0XzEBXaPohFccW8ukM0BG17P/VwQkUr26ychLV3ksz2Ii/yHGdJZs5kILGkLdVavhDKHIe+9Bwy5Ck4SlPyekwHGy6IdWa8QRQE6ShFoyaxKqw5PMXlcGyjgnHti7ZjKCC37t0Da/22MEJufpdcaI2KrE/7VYfV+o79n6qK56RqQmGacrD50MN4w2m6NasP9f8AM+lL991Cad16MBClc7gDjEiYeHLMrijax8tm3yVS1u3giiS/IGruu5rlPSIwOQDKsjM2tJ1+TBxgDrgJPJnh/7PBXWY43LDqGHoHk7tMYOH7BXCHNc2XB4WRBQt3TR9pMZYTFhzUnqtOURuZLCEAVN7KaIGo1rRAJb9zbiHCp1u9vRTeooNhmMOoFHuWzcv3RIbyrH9awwG0SJ7z0lklBv3RkCvsMQsV3Xj/NRWeJOSgAIMBT+PGWytNOogzjTrYV1tyM2IhbXDkObaiFlg9rWmtrbszx7OoYTyZmfV1ulxxQGRpvpqT7eZ6hjBD0HryWJjKTaHULXPWMR2eugkQgc3REpBqpRH/RPNLMBJbCO3fz/9rMS9VKVOXx1nY0AWrbaXxjjrDARmo3xjhv8HuZ9FNLGAhAn0LPHFoTcL2sDy1F1qqStE0JRzu41gBTZR1sfw7CoQH72kNIttzNAx4KYketSJN7ywNOV9qjFdHWvboVuRE9KF1qD7FROTLeeIeig9ag9Ysv3HJqQyc1KUBW03jF8qA4Ypnwru28D3KNsdhCMMZ3ucRhVGGfTknMHJx5ago0nmirHWp7qW1Ej03JLg4x3iIlm/3RSW0+pYzVwIpzFt5UBdlvbkARYtJ6eaWG5cSPnoSAFyfpLxWQ9ThwVBetRJx03W2ZdDegLO+Ngg0GSwzX476CvwtKbcT5gfNvxxRaP0aHcwWGuKdT5amIFpv5oaIuRlJJUQZ7quRBvQjH/Mwixf85f0ghlgzLkTYGD9EgBj3HIpaXbUZmQphOjuEhu11e9hmZY3iFnPAk2B4NsD6dzUaz5t7KWC69Pq89yTmePqDMdTYdzV/nSfxZm1ENv/IgkjUyjqcyPugQoqAk9WXR8xYOK7UVBSPMVlcswUoi+rDPzbF5w1wl5GK1rJ45JLsYzXrApXiLge3Bbc/Hmpa9ihLw21cZ9GVycRoqZlBVLlexVgklQqJwIOXTbXxXFVPesWGhdmJye/JGpKwgyeTs4j3U7txFglFm9G5jQk27xF4=" />
</div>

<script type="text/javascript">
//<![CDATA[
var theForm = document.forms['aspnetForm'];
if (!theForm) {
    theForm = document.aspnetForm;
}
function __doPostBack(eventTarget, eventArgument) {
    if (!theForm.onsubmit || (theForm.onsubmit() != false)) {
        theForm.__EVENTTARGET.value = eventTarget;
        theForm.__EVENTARGUMENT.value = eventArgument;
        theForm.submit();
    }
}
//]]>
</script>


<script src="/WebResource.axd?d=EzGTOGwoKDVHNpRhi1u2800TzZlL8E0YANrRQPWV1YHHzn8qvnZtZU2XMBrH2gFW3de9oBFxqwj4avG4iFQ5uIu7FHlRZg_Aa0unc0d1gFQ1&amp;t=637811765229275428" type="text/javascript"></script>


<script src="/ScriptResource.axd?d=B2bV4s4lds5IGGbJizqEnRDwC4ReBMU5YprUehGUHFXGyvlIreKu5v3B9SsPch13zV4IpCXbzFgJOF-L19Ml4dFr74_yAzQv1xN4Lw949SPU3FmdSszM1gAVyXTBt2QNVzl38mplC-oEP723LVBMKQ2&amp;t=2265eaa7" type="text/javascript"></script>
<script type="text/javascript">
//<![CDATA[
var __cultureInfo = {"name":"sl-SI","numberFormat":{"CurrencyDecimalDigits":2,"CurrencyDecimalSeparator":",","IsReadOnly":true,"CurrencyGroupSizes":[3],"NumberGroupSizes":[3],"PercentGroupSizes":[3],"CurrencyGroupSeparator":".","CurrencySymbol":"€","NaNSymbol":"NaN","CurrencyNegativePattern":8,"NumberNegativePattern":1,"PercentPositivePattern":0,"PercentNegativePattern":0,"NegativeInfinitySymbol":"-∞","NegativeSign":"-","NumberDecimalDigits":2,"NumberDecimalSeparator":",","NumberGroupSeparator":".","CurrencyPositivePattern":3,"PositiveInfinitySymbol":"∞","PositiveSign":"+","PercentDecimalDigits":2,"PercentDecimalSeparator":",","PercentGroupSeparator":".","PercentSymbol":"%","PerMilleSymbol":"‰","NativeDigits":["0","1","2","3","4","5","6","7","8","9"],"DigitSubstitution":1},"dateTimeFormat":{"AMDesignator":"dop.","Calendar":{"MinSupportedDateTime":"\/Date(-62135596800000)\/","MaxSupportedDateTime":"\/Date(253402297199999)\/","AlgorithmType":1,"CalendarType":1,"Eras":[1],"TwoDigitYearMax":2029,"IsReadOnly":true},"DateSeparator":". ","FirstDayOfWeek":1,"CalendarWeekRule":0,"FullDateTimePattern":"dddd, dd. MMMM yyyy HH:mm:ss","LongDatePattern":"dddd, dd. MMMM yyyy","LongTimePattern":"HH:mm:ss","MonthDayPattern":"d. MMMM","PMDesignator":"pop.","RFC1123Pattern":"ddd, dd MMM yyyy HH\u0027:\u0027mm\u0027:\u0027ss \u0027GMT\u0027","ShortDatePattern":"d. MM. yyyy","ShortTimePattern":"HH:mm","SortableDateTimePattern":"yyyy\u0027-\u0027MM\u0027-\u0027dd\u0027T\u0027HH\u0027:\u0027mm\u0027:\u0027ss","TimeSeparator":":","UniversalSortableDateTimePattern":"yyyy\u0027-\u0027MM\u0027-\u0027dd HH\u0027:\u0027mm\u0027:\u0027ss\u0027Z\u0027","YearMonthPattern":"MMMM yyyy","AbbreviatedDayNames":["ned.","pon.","tor.","sre.","čet.","pet.","sob."],"ShortestDayNames":["ned.","pon.","tor.","sre.","čet.","pet.","sob."],"DayNames":["nedelja","ponedeljek","torek","sreda","četrtek","petek","sobota"],"AbbreviatedMonthNames":["jan.","feb.","mar.","apr.","maj","jun.","jul.","avg.","sep.","okt.","nov.","dec.",""],"MonthNames":["januar","februar","marec","april","maj","junij","julij","avgust","september","oktober","november","december",""],"IsReadOnly":true,"NativeCalendarName":"gregorijanski koledar","AbbreviatedMonthGenitiveNames":["jan.","feb.","mar.","apr.","maj","jun.","jul.","avg.","sep.","okt.","nov.","dec.",""],"MonthGenitiveNames":["januar","februar","marec","april","maj","junij","julij","avgust","september","oktober","november","december",""]},"eras":[1,"po Kr.",null,0]};//]]>
</script>

<script src="/ScriptResource.axd?d=wq1Anz49sp2zuAUowprkqh46swvaZPCx2mjX8G0Fic-KJfqVb5qmDtRGcNY58CXFTlst__0lS45i7OviEsIAl9-gFO-pd-QdE6GzNOKo9H0tQEs0GoBgoev8rXWKvp130&amp;t=3a1336b1" type="text/javascript"></script>
<script src="/ScriptResource.axd?d=wSzQVfmXSx1Tr0zy9kDXnUYwztPMfyeMd_U7J8rMUOHSfl9run-033LZqNtB233owwSLjBiFo2Y7cS1glgyDyisV-mYR7Gav7RwS11Dnyenh9myAF5L4t2_NC-oSWGZAmYNUGC9c35ca7YXALlej4Q2&amp;t=3a1336b1" type="text/javascript"></script>
<div>

	<input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="9B35964F" />
	<input type="hidden" name="__VIEWSTATEENCRYPTED" id="__VIEWSTATEENCRYPTED" value="" />
	<input type="hidden" name="__PREVIOUSPAGE" id="__PREVIOUSPAGE" value="Uand7pVg34OKZ3N4eOSSTiNdqSZsC7d7cBk4fzMyjh1DJRVOAZzmSoa7bRR7xUp078rdOk-Cv0hYT0So7jjXFa5Hk0hAOCyqh6siGWd9lnJshVHdwnrlZ8QnHzm4QTsj0" />
	<input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="IJx/SwZpvSmmHsz2cIjZ/pJYh/FnOunuCtQTxHFos2hoj++Pz5UAznw5QMZPCZYMx9J/OxSwJJztzVBmmo327XQl1G2xMrmLlIragPg5bhd9+6dpS5JOgwHzi5K5Ws/xuaaThUT4vT20j6fgp7uWMRYGhEacKRNYek1RsFhKENBhnMZp+iI4KBcDwYiNL37g7WdGF8UjpiusE2TYvIM0dlJL75IBxvaf9O+dqCia8pf4OnRgeoJl82JBHFwrxeknvT+PcCM9W9gQKKmrJi8nxzWr7RuEu1Q3uRIga6JylGTYBDe+tY5fmoUv1ltLEB7J" />
</div>
    <script type="text/javascript">
//<![CDATA[
Sys.WebForms.PageRequestManager._initialize('ctl00$ScriptManagerMaster', 'aspnetForm', ['tctl00$UpdatePanel3',''], [], [], 90, 'ctl00');
//]]>
</script>

    
    <input type="hidden" name="ctl00$hfUserAlert" id="ctl00_hfUserAlert" value="false" />
    <div id="divBody">
      <div id="divHeader">
        <div class="divHeadLogoImg">
          <img id="ctl00_imgBack" src="../../App_Themes/Images/Backgrounds/gimb-logo-90.png" style="border-width:0px;padding-top: 2px;" />
        </div>
        <div class="gPad4TRL" style="overflow: hidden;">
          <div class="gFloatLeft collapse-hide-s caption-lg">
            Gimnazija <strong>Bežigrad</strong>
          </div>
          
          <div id="divMasterUser" class="divMenuTool">
            <div id="divMasterUserTitle" class="divMenuToolTitle gPadLR8">
              <span id="ctl00_lblLoginName">Mark Marjanović</span>
              
            </div>
            <div id="ctl00_divMasterUserInner" class="gAlignLeft divInner gPad4">
              <div>
                <a class=" csbuttonmodern" href="javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions(&quot;ctl00$ctl03&quot;, &quot;&quot;, false, &quot;&quot;, &quot;../Uporabnik/Profil.aspx&quot;, false, true))" style="width: 100%;"><span class='cstxt csnoimg'>Uredi profil</span></a>
              </div>
              <div>
                <a id="ctl00_btnLoginStatus" class="csbuttonmodern csb_cancel" href="javascript:__doPostBack(&#39;ctl00$btnLoginStatus$ctl00&#39;,&#39;&#39;)" style="width: 100%;">Odjava</a>
              </div>
            </div>
          </div>
        </div>
        <div id="divMenuIn">
          <div id="ctl00_divOsebaPregled" class="divOseba embed">
            <div id="ctl00_divCustomLinks" class="collapse-hide" style="float: right;"><a class="csbuttonmodern " href="https://www.gimb.org/" target="_blank"><span class='cstxt csnoimg'>Domača stran</span></a><a class="csbuttonmodern " href="https://gimnazijabezigrad.sharepoint.com" target="_blank"><span class='cstxt csnoimg'>Intranet</span></a><a class="csbuttonmodern " href="https://ucilnice.gimb.org" target="_blank"><span class='cstxt csnoimg'>E-učilnica</span></a><a class="csbuttonmodern csb_blue" href="https://www.gimb.org/wp-content/uploads/2016/12/GimSIS-navodila_za_uporabo_v2.pdf" target="_blank"><span class='cstxt csnoimg'>Navodila / Instructions</span></a><a class="csbuttonmodern csb_blue" href="mailto:pomoc.gimsis@gimb.org" target=""><span class='cstxt csnoimg'>Pomoč...</span></a></div>

            <span class="collapse-hide-s">Izbrana oseba:</span>
            <select name="ctl00$ddlOseba" onchange="javascript:setTimeout(&#39;__doPostBack(\&#39;ctl00$ddlOseba\&#39;,\&#39;\&#39;)&#39;, 0)" id="ctl00_ddlOseba">
	<option selected="selected" value="0">Mark Marjanović (učenec 1.A)</option>

</select>

            2022/2023
          </div>
          <div class="horzMenuExDiv embedwhole">
            <div class="menu-collapse"></div>

            

            <div class="horzMenuEx" id="ctl00_menMain">
	<ul class="level1">
		<li><a class="level1 vertMenuS" href="/Default.aspx">Prva stran</a></li><li><a class="level2 vertMenuS" href="/Page_Gim/Ucenec/DnevnikUcenec.aspx">Urnik</a></li><li><a class="level2 vertMenuS" href="/Page_Gim/Ucenec/IzpitiUcenec.aspx">Ocenjevanja</a></li><li><a class="level2 vertMenuS selected" href="/Page_Gim/Ucenec/OceneUcenec.aspx">Ocene</a></li><li><a class="level2 vertMenuS" href="/Page_Gim/Ucenec/IzostankiUcenec.aspx">Odsotnost</a></li><li><a class="level2 vertMenuS" href="/Page_Gim/Ucenec/UciteljskiZbor.aspx">Učitelji</a></li><li><a class="level2 vertMenuS" href="/Page_Gim/Uporabnik/Sporocila.aspx">Sporočila</a></li><li><a class="popout level2 vertMenuS">Ostalo</a><ul class="level3 gMenuFixZOrder vertMenuDMen">
			<li><a class="level3 vertMenuD" href="Ucbeniki.aspx">Učbeniški sklad</a></li><li><a class="level3 vertMenuD" href="Prijave.aspx">Prijave</a></li>
		</ul></li>
	</ul>
</div>

          </div>
          
        </div>

      </div>
      <div id="divBodyIn">
        <div id="divInnerContent" class="divCenter">
          
          <div id="ctl00_divPageInner" class="divBoxIn">
            
            
            <div id="ctl00_UpdatePanel3">
	
                
  
  
  <div class="divPageBody">
    <div class="divInputBar">
      Šolsko leto
      <select name="ctl00$ContentPlaceHolder1$ddlIdSolskoleto" onchange="javascript:setTimeout(&#39;__doPostBack(\&#39;ctl00$ContentPlaceHolder1$ddlIdSolskoleto\&#39;,\&#39;\&#39;)&#39;, 0)" id="ctl00_ContentPlaceHolder1_ddlIdSolskoleto">
		<option selected="selected" value="2022">2022/2023</option>

	</select>
    </div>
    <div id="divPrintContent">
      <div class="divPrintHeader">
        
        Gimnazija <b>Bežigrad</b>
        <span style="font-size: 90%; float: right;">1. 04. 2023 10:47:31</span>
        <br />
        <br />
        
        <div class="gAlignCenter">
          <b>
            Mark Marjanović</b> (1.A): Ocene v šolskem
          letu
          2022/2023
          <br />
          <br />
        </div>
      </div>
      <div id="tabs">
        <a id="btnVnosKomentar" class="csbutton csb_action gFloatRight" style="display: none !important;" href="modVnosPorociloKomentar.aspx">VNOS</a>
        <ul>
          <li><a href="#tabOcene"><span>Ocene</span></a></li>
          <li><a href="#tabSkupine"><span>Razredi/skupine</span></a></li>
        </ul>
        <div id="tabOcene">
          <div id="ctl00_ContentPlaceHolder1_grdOcene" DBFieldDayId="DatKoledar" ShowDate="False" ShowNext="False" ShowPrevious="False" ShowSaturday="False" ShowSunday="False" SingleDay="True">
		<table class="tabelaUrnik" border="0" style="width:;">
			<thead>
				<tr>
					<th>Predmet</th><th><span>Gimn., 1. ocenjevalno obdobje</span></th><th><span>Gimn., 2. ocenjevalno obdobje</span></th><th><span>Gimn., Spomladanski izpitni rok</span></th><th><span>Gimn., Jesenski izpitni rok</span></th>
				</tr>
			</thead><tbody>
				<tr>
					<th class="fixedCol"><b>Slovenščina</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_0_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 07.11.2022
Učitelj: Mojca Osvald
Predmet: Slovenščina
Ocenjevanje: Pisno ocenjevanje znanja
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: Jezik, sporazumevanje, glasoslovje, pravopis' class="txtOcena ocZadnja oc3">3</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_0_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 21.12.2022
Učitelj: Mojca Osvald
Predmet: Slovenščina
Ocenjevanje: Prva šolska naloga
Vrsta: Pisno ocenjevanje - 2. rok ()
Rok: Utemeljevalni spis' class="txtOcena ocZadnja oc3">3</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_0_0_2" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 15.12.2022
Učitelj: Mojca Osvald
Predmet: Slovenščina
Ocenjevanje: Govorni nastop
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: Književnost in slovnica - snov prvega letnika' class="txtOcena ocZadnja oc3">3</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_0_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 23.02.2023
Učitelj: Mojca Osvald
Predmet: Slovenščina
Ocenjevanje: Druga šolska naloga
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: Tvorba neumetnostnega besedila' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_0_1_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 30.03.2023
Učitelj: Mojca Osvald
Predmet: Slovenščina
Ocenjevanje: Ustno ocenjevanje znanja
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: Književnost prvega letnika' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Matematika</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_1_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 19.10.2022
Učitelj: Urška Markun
Predmet: Matematika
Ocenjevanje: 1. kontrolna naloga
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocZadnja oc3">3</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_1_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Začasna ocena: 14.12.2022
Učitelj: Urška Markun
Predmet: Matematika
Ocenjevanje: 2. kontrolna naloga
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocVmesna oc2">2</span>, <span title='Ocena: 06.01.2023
Učitelj: Urška Markun
Predmet: Matematika
Ocenjevanje: 2. kontrolna naloga
Vrsta: Pisno ocenjevanje - 2. rok ()
Rok: ' class="txtOcena ocZadnja oc3">3</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_1_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 15.02.2023
Učitelj: Urška Markun
Predmet: Matematika
Ocenjevanje: 3. kontrolna naloga
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocZadnja oc3">3</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Angleščina</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_2_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 07.11.2022
Učitelj: Maja Petričić Štritof
Predmet: Angleščina
Ocenjevanje: 
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_2_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 14.11.2022
Učitelj: Maja Petričić Štritof
Predmet: Angleščina
Ocenjevanje: Individual oral presentation
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: ' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div></td><td class="col1 ">&nbsp;</td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Nemščina</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_3_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 12.01.2023
Učitelj: Barbara Ovsenik Dolinar
Predmet: Nemščina
Ocenjevanje: 
Vrsta: Pisno ocenjevanje - 2. rok ()
Rok: ' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_3_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 11.01.2023
Učitelj: Barbara Ovsenik Dolinar
Predmet: Nemščina
Ocenjevanje: 
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: ' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col1 ">&nbsp;</td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Zgodovina</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_4_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 05.12.2022
Učitelj: Dragica Marinko
Predmet: Zgodovina
Ocenjevanje: Prve civilizacije
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_4_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 07.11.2022
Učitelj: Dragica Marinko
Predmet: Zgodovina
Ocenjevanje: Zgodovinska obdobja
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: ' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col1 ">&nbsp;</td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Športna vzgoja</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_5_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 21.12.2022
Učitelj: Milan Bizjan
Predmet: Športna vzgoja
Ocenjevanje: Fitnes
Vrsta: Drugo ocenjevanje - 1. ocena ()
Rok: fitnes' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_5_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 09.01.2023
Učitelj: Milan Bizjan
Predmet: Športna vzgoja
Ocenjevanje: Odbojka, igra
Vrsta: Drugo ocenjevanje - 1. ocena ()
Rok: Odbojka, igra' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div></td><td class="col1 ">&nbsp;</td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Glasba</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_6_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 22.12.2022
Učitelj: Kristina Drnovšek
Predmet: Glasba
Ocenjevanje: 
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_6_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 17.03.2023
Učitelj: Kristina Drnovšek
Predmet: Glasba
Ocenjevanje: 
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: ' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Likovna umetnost</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_7_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 07.12.2022
Učitelj: Tanja Mastnak
Predmet: Likovna umetnost
Ocenjevanje: Prvi test: analiza
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: Prvi test: analiza likovnega dela' class="txtOcena ocZadnja oc3">3</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_7_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 28.02.2023
Učitelj: Tanja Mastnak
Predmet: Likovna umetnost
Ocenjevanje: Referati
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: Referati' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Geografija</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_8_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 15.11.2022
Učitelj: Veronika Lazarini
Predmet: Geografija
Ocenjevanje: Zgradba zemlje, relief
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_8_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 13.12.2022
Učitelj: Veronika Lazarini
Predmet: Geografija
Ocenjevanje: 
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: ' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_8_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Začasna ocena: 29.03.2023
Učitelj: Veronika Lazarini
Predmet: Geografija
Ocenjevanje: Podnebje, rastje, prst
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocVmesna oc4">4</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Biologija</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_9_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 27.10.2022
Učitelj: Polona Gros Remec
Predmet: Biologija
Ocenjevanje: Biologija kot znanost, atomi, gradbeni elementi snovi, voda, ogljikovi hidrati, lipidi, beljakovine, nukleinske kisline, laboratorijske vaje (mikroskopiranje, dokaz org. snovi)
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_9_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 01.12.2022
Učitelj: Polona Gros Remec
Predmet: Biologija
Ocenjevanje: Koncepti biologije (9 konceptov je vseh skupaj), zgradba in naloge organelov evkariontske celice
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: Koncepti biologije (9 konceptov je vseh skupaj), zgradba in naloge organelov evkariontske celice' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_9_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Začasna ocena: 09.03.2023
Učitelj: Polona Gros Remec
Predmet: Biologija
Ocenjevanje: Prokariontska celica (3.2), Transport snovi skozi membrano (4.1), Celica in energija (4.2), Celično dihanje (5.1), laboratorijske vaje
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: ' class="txtOcena ocVmesna oc4">4</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Kemija</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_10_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 26.11.2022
Učitelj: Saša Cecowski
Predmet: Kemija
Ocenjevanje: 1. test
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: 1. test' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_10_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 12.01.2023
Učitelj: Saša Cecowski
Predmet: Kemija
Ocenjevanje: 
Vrsta: Ustno ocenjevanje - 1. ocena ()
Rok: ' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_10_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 28.02.2023
Učitelj: Saša Cecowski
Predmet: Kemija
Ocenjevanje: 2. test
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: 2. test' class="txtOcena ocZadnja oc4">4</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Fizika</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_11_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 24.11.2022
Učitelj: Monika Vidmar
Predmet: Fizika
Ocenjevanje: 1. test
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: merjenja, premo gibanje' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_11_0_1" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 25.11.2022
Učitelj: Monika Vidmar
Predmet: Fizika
Ocenjevanje: Za osvojeno priznanje Čmrlj
Vrsta: Drugo ocenjevanje - 1. ocena ()
Rok: Za osvojeno priznanje Čmrlj' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div></td><td class="col1 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_11_1_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 20.02.2023
Učitelj: Monika Vidmar
Predmet: Fizika
Ocenjevanje: 2. test
Vrsta: Pisno ocenjevanje - 1. rok ()
Rok: Pospešeno gibanje, meti, relativnost gibanja, kroženje' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div></td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr><tr>
					<th class="fixedCol"><b>Informatika</b></th><td class="col0 "><div class="divCellData dzNeObstaja ">
						<span id="ctl00_ContentPlaceHolder1_grdOcene_btnCell_12_0_0" title="Ocena: "><span class='txtVOcObd'><span title='Ocena: 17.11.2022
Učitelj: Andrej Šuštaršič
Predmet: Informatika - vaje
Ocenjevanje: Kombinirano ocenjevanje
Vrsta: Drugo ocenjevanje - 1. ocena ()
Rok: ' class="txtOcena ocZadnja oc5">5</span></span></span>
					</div></td><td class="col1 ">&nbsp;</td><td class="col2 ">&nbsp;</td><td class="col3 ">&nbsp;</td>
				</tr>
			</tbody>
		</table>
	</div>
        </div>
        <div id="tabSkupine">
          <div>
		<table class="tabela tdRowSelect" cellspacing="0" rules="all" border="1" id="ctl00_ContentPlaceHolder1_gvwUcenecRazredi" style="border-collapse:collapse;">
			<thead>
				<tr>
					<th scope="col">Razred/Skupina</th><th scope="col">Šolsko leto</th><th scope="col">Šola/program</th><th scope="col">Letnik</th><th scope="col">Razrednik(i)</th>
				</tr>
			</thead><tbody>
				<tr onclick="gvwUcenecRazrediSelectRow(this, 0);">
					<td style="width:100px;">
                  <div class="RH">
                    1.A
                  </div>
                </td><td>2022/2023</td><td>Gimnazija</td><td>1. letnik</td><td>Saša Cecowski</td>
				</tr><tr class="alt" onclick="gvwUcenecRazrediSelectRow(this, 1);">
					<td style="width:100px;">
                  <div class="SH">
                    1.A_ŠVZ-M
                  </div>
                </td><td>2022/2023</td><td>Gimnazija</td><td>1. letnik</td><td> </td>
				</tr><tr onclick="gvwUcenecRazrediSelectRow(this, 2);">
					<td style="width:100px;">
                  <div class="SH">
                    1.As2
                  </div>
                </td><td>2022/2023</td><td>Gimnazija</td><td>1. letnik</td><td> </td>
				</tr>
			</tbody><tfoot>

			</tfoot>
		</table>
	</div>
        </div>
      </div>
    </div>
  </div>

              
</div>
            
            
          </div>
        </div>
      </div>
      <div id="divFooter">
        <div id="divFooterInner">
          <div id="divFooterLeft" class="g8pt gFloatLeft">
          </div>
          <div id="divFooterRight" class="g8pt gFloatRight">
            <a id="ctl00_btnAbout" href="javascript:WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions(&quot;ctl00$btnAbout&quot;, &quot;&quot;, false, &quot;&quot;, &quot;../../About.aspx&quot;, false, true))">Copyright © 2011-2023 M. &amp; B.</a>
          </div>
          <div id="divFooterCenter" class="g8pt gAlignCenter">
            &nbsp;
          </div>
        </div>
      </div>
    </div>
  

<script type="text/javascript">
//<![CDATA[
(function() {var fn = function() {$get("ctl00_ScriptManagerMaster_HiddenField").value = '';Sys.Application.remove_init(fn);};Sys.Application.add_init(fn);})();//]]>
</script>
<script type='text/javascript'>new Sys.WebForms.Menu({ element: 'ctl00_menMain', disappearAfter: 500, orientation: 'horizontal', tabIndex: 0, disabled: false });</script>
<script type="text/javascript">
//<![CDATA[
function gvwUcenecRazrediSelectRow(aEl, aRowIndex) {
                if (window['gssCanSelectRow'] == undefined) {
                  gssCanSelectRow = true;                
                }
                if (gssCanSelectRow == true) {
                  if (aEl.tagName.toUpperCase() != 'TR') {
                    while (aEl.parentNode != null && aEl.tagName.toUpperCase() != 'TR') {
                      aEl = aEl.parentNode;
                    }
                  }
                  if (aEl.tagName.toUpperCase() == 'TR') {
                    var bSelected = false;
                    if (aEl != null) {
                      bSelected = aEl.className == 'selected';
                    }
                    if (aRowIndex != null && aRowIndex >= 0 && !bSelected) { 
                       __doPostBack('ctl00$ContentPlaceHolder1$gvwUcenecRazredi','Select$' + aRowIndex)
                    }
                  }
                }
                gssCanSelectRow = true;
              }//]]>
</script>
</form>
  
  
</body>
</html>
"""
get_grades(get)