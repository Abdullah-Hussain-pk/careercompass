export async function api<T=any>(path:string,method='GET',body?:unknown,retry=true):Promise<T>{
 const response=await fetch(`/api${path}`,{method,credentials:'include',headers:{'Content-Type':'application/json','X-CareerCompass':'1'},body:body===undefined?undefined:JSON.stringify(body)});
 if(response.status===401&&retry&&!path.startsWith('/auth/')){
  const refreshed=await fetch('/api/auth/refresh',{method:'POST',credentials:'include',headers:{'X-CareerCompass':'1'}});
  if(refreshed.ok)return api<T>(path,method,body,false);
 }
 const data=await response.json().catch(()=>({message:'Unexpected server response. Check that the API is running.'}));
 if(!response.ok)throw new Error(data.message??'The request failed.');return data;
}
