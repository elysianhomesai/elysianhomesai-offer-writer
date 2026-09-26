const $=s=>document.querySelector(s);
let current=null;
const money=v=>typeof v==="number"&&v>=1000?"$"+v.toLocaleString():v;
function display(c){
  if(c.value===null||c.value==="") return "Not provided";
  if(c.key==="inspection") return c.value?"Elected":"Declined";
  if(c.key==="down_payment_percent") return c.value+"%";
  if(c.key==="financing_type") return String(c.value).charAt(0).toUpperCase()+String(c.value).slice(1)+" Financing";
  return money(c.value);
}
$("#form").addEventListener("submit",async e=>{
  e.preventDefault();const btn=e.submitter;btn.disabled=true;btn.textContent="Preparing…";
  try{
    const r=await fetch("/api/intake",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mls_number:$("#mls").value,buyers:$("#buyers").value,offer_text:$("#offer").value})});
    if(!r.ok)throw new Error("Unable to prepare offer");
    render(await r.json());
  }catch(err){alert(err.message)}
  finally{btn.disabled=false;btn.innerHTML='Prepare Offer <span>→</span>'}
});
function inputFor(c){
  if(c.key==="mortgage_commitment_date") return '<input class="missing-input" data-key="'+c.key+'" type="date" required>';
  if(c.key==="offer_expiration") return '<input class="missing-input" data-key="'+c.key+'" type="datetime-local" required>';
  if(c.key==="closing_date") return '<input class="missing-input" data-key="'+c.key+'" type="date" required>';
  if(c.key==="inspection_days") return '<input class="missing-input" data-key="'+c.key+'" type="number" min="0" required>';
  return '<input class="missing-input" data-key="'+c.key+'" type="text" required>';
}
function render(d){
  current=d;
  $("#intake").classList.add("hidden");$("#review").classList.remove("hidden");
  $("#reviewTitle").textContent=d.offer.mls_number+" — "+d.offer.buyers.map(x=>x.name).join(", ");
  const missing=d.checks.filter(x=>x.status!=="complete");
  $("#status").innerHTML='<div class="summary '+(d.ready?"ready":"needs")+'">'+(d.ready?"✓ OFFER READY":"⚠ "+missing.length+" item"+(missing.length===1?"":"s")+" still needed")+"</div>";
  $("#checks").innerHTML=d.checks.map(c=>'<div class="check '+c.status+'"><div class="icon">'+(c.status==="complete"?"✓":"!")+'</div><div><strong>'+c.label+'</strong>'+(c.reason?'<div class="reason">'+c.reason+"</div>":"")+'</div><div class="value">'+(c.status==="complete"?display(c):inputFor(c))+"</div></div>").join("");
  $("#continueWrap").innerHTML=d.ready?'<div class="ready-note">All required V1 offer terms are complete. Nothing has been sent to TransactionDesk.</div>':'<button id="continue">Continue <span>→</span></button>';
  const b=$("#continue");if(b)b.onclick=submitClarifications;
  window.scrollTo({top:0,behavior:"smooth"});
}
async function submitClarifications(){
  const btn=$("#continue");btn.disabled=true;btn.textContent="Checking…";
  const updates={};
  document.querySelectorAll(".missing-input").forEach(i=>{if(i.value)updates[i.dataset.key]=i.type==="number"?Number(i.value):i.value});
  try{
    const r=await fetch("/api/clarify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({offer:current.offer,updates})});
    if(!r.ok)throw new Error("Unable to update offer");
    render(await r.json());
  }catch(err){alert(err.message);btn.disabled=false;btn.innerHTML='Continue <span>→</span>'}
}
$("#edit").onclick=()=>{$("#review").classList.add("hidden");$("#intake").classList.remove("hidden")};
