from dataclasses import replace
from decimal import Decimal
import pytest
from ceab.eproc import Eproc
from ceab.models import AutomationError, Benefit
from ceab.rules import EVENTS
from ceab import selectors as S
from conftest import NUMBERS

B = Benefit(NUMBERS[0],'CONCESSAO','Teste','22/04/2025','01/09/2026',amount=Decimal('100'))


def untouched(page):
    return page.locator('#txtRMI123456789,#txtDataInicioIncapacidade123456789,#txtCID123456789,#chkDippd123456789,input[type=radio],#parte,#prazo').evaluate_all('(els)=>els.map(x=>({value:x.value,checked:x.checked}))')


def test_fill_preserves_fields_and_test_never_submits(context,site):
    url,counts = site
    page = context.new_page()
    page.goto(url+'/form?num_processo='+B.process)
    original = untouched(page)
    adapter = Eproc(context)
    adapter.fill(page,B,False)
    assert page.locator(S.FIELDS['dib']).input_value() == B.dib
    assert page.locator('#selLocalizadorDesativar option:checked').count() == 2
    assert page.evaluate('window.changed') == 1
    assert untouched(page) == original
    edited = replace(B,dib='23/04/2025',dcb='30/09/2028')
    assert adapter.submit(page,edited,True) is False
    assert counts['sent'] == 0
    assert page.locator(S.SUBMIT).count() == 1
    assert page.locator(S.FIELDS['dib']).input_value() == edited.dib
    assert page.locator(S.FIELDS['dcb']).input_value() == edited.dcb
    assert untouched(page) == original


def test_submit_confirm_and_minute(context,site):
    url,counts = site
    page = context.new_page()
    page.goto(url+'/form?num_processo='+B.process)
    adapter = Eproc(context)
    assert adapter.submit(page,B,False)
    assert counts['sent'] == 1
    adapter.minute(page,B.process,False)
    assert counts['minute'] == 1


def test_validation_alert_is_send_error(context,site):
    url,counts = site
    page = context.new_page()
    page.goto(url+'/form?num_processo='+B.process)
    page.evaluate('window.validation=true')
    with pytest.raises(AutomationError, match='Prazo inválido') as exc:
        Eproc(context).submit(page,B,False)
    assert exc.value.code == 'ERRO_ENVIO'
    assert counts['sent'] == 0
    assert page.locator(S.SUBMIT).count() == 1


def test_queue_already_checked_is_not_toggled(context,site):
    url,_ = site
    queue = context.new_page()
    queue.goto(url+'/queue')
    adapter = Eproc(context)
    pages = adapter.open_queue()
    assert len(pages) == 3
    assert not queue.evaluate('window.toggles')
    assert {adapter.identify(p) for p in pages} == set(NUMBERS)
    b,label = adapter.read_document(pages[0],NUMBERS[0])
    assert b.amount == Decimal('100')
    assert 'evento 26' in label
    assert len(context.pages) == 4  # wrapper fechado; fila + 3 processos


def test_partial_queue_becomes_all_checked(context,site):
    url,_ = site
    queue = context.new_page()
    queue.goto(url+'/queue?count=1')
    queue.locator(S.QUEUE_ROWS).uncheck()
    assert len(Eproc(context).open_queue()) == 1
    assert queue.evaluate('window.toggles') == 1
    assert queue.locator(S.QUEUE_ROWS).is_checked()


def test_process_mismatch_blocks_fill(context,site):
    url,_ = site
    page = context.new_page()
    page.goto(url+'/form?num_processo='+NUMBERS[1])
    with pytest.raises(AutomationError) as exc: Eproc(context).fill(page,B,False)
    assert exc.value.code == 'PROCESSO_DIVERGENTE'


def test_mask_fallback_and_divergence(context,site):
    url,_ = site
    page = context.new_page()
    page.goto(url+'/form?num_processo='+B.process)
    field = page.locator(S.FIELDS['dib'])
    field.evaluate('''el=>{el.addEventListener('blur',()=>{if(!el.dataset.once){el.value='';el.dataset.once='1'}});el.addEventListener('input',()=>{if(el.dataset.once){const n=el.value.replace(/\\D/g,'').slice(0,8);el.value=n.slice(0,2)+(n.length>2?'/'+n.slice(2,4):'')+(n.length>4?'/'+n.slice(4):'')}})}''')
    Eproc(context).fill_verified(field,B.dib,'dib')
    assert field.input_value() == B.dib
    field.evaluate("el=>el.addEventListener('blur',()=>el.value='errado')")
    with pytest.raises(AutomationError) as exc: Eproc(context).fill_verified(field,B.dib,'dib')
    assert exc.value.code == 'PREENCHIMENTO_DIVERGENTE'


def test_text_of_selected_option_must_match(context,site):
    url,_ = site
    page = context.new_page()
    page.goto(url+'/form?num_processo='+B.process)
    page.locator(f'option[value="{EVENTS[B.kind][0]}"]').evaluate("el=>el.textContent='Outro evento'")
    with pytest.raises(AutomationError) as exc: Eproc(context).fill(page,B,False)
    assert exc.value.code == 'PREENCHIMENTO_DIVERGENTE'


def test_form_in_iframe(context,site):
    url,counts=site
    page=context.new_page()
    page.goto(url+'/process?num_processo='+B.process)
    page.set_content(f'<iframe src="{url}/form?num_processo={B.process}"></iframe>')
    frame=page.frame_locator('iframe')
    frame.locator(S.EVENT).wait_for()
    Eproc(context).fill(page,B,False)
    assert frame.locator(S.FIELDS['dib']).input_value()==B.dib
    assert not Eproc(context).submit(page,B,True)
    assert counts['sent']==0


def test_newest_first_document_preferred(context,site):
    url,_=site
    page=context.new_page()
    page.goto(url+'/process?num_processo='+B.process)
    page.set_content('''<table>
    <tr><td>Contestação</td><td><a class="infraLinkDocumento" href="/wrapper?SeqDocumento=1&numSeqEvento=40">CONT1</a></td></tr>
    <tr><td><a class="infraLinkDocumento" data-nome="PROACORDO" href="/wrapper?SeqDocumento=1&numSeqEvento=26">PROACORDO1</a></td></tr>
    <tr><td><a class="infraLinkDocumento" data-nome="PROACORDO" href="/wrapper?SeqDocumento=1&numSeqEvento=30">PROACORDO1</a></td></tr>
    <tr><td><a class="infraLinkDocumento" data-nome="PROACORDO" href="/wrapper?SeqDocumento=2&numSeqEvento=50">PROACORDO2</a></td></tr>
    </table>''')
    selected,label=Eproc(context).document_link(page,B.process)
    assert 'numSeqEvento=30' in selected
    assert 'evento 30' in label
    page.locator('[data-nome="PROACORDO"]').evaluate_all('(els)=>els.forEach(el=>el.remove())')
    selected,label=Eproc(context).document_link(page,B.process)
    assert 'numSeqEvento=40' in selected


def test_minute_dry_run_checks_preference_without_saving(context,site):
    url,counts=site
    page=context.new_page()
    page.goto(url+'/form?num_processo='+B.process)
    Eproc(context).minute(page,B.process,True,source_url=url+'/process?num_processo='+B.process)
    assert counts['minute']==0
    assert len(context.pages)==1
    assert '/form?' in page.url
