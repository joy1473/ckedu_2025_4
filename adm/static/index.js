$(() => {
  // 관리자 인증 사용 여부
  const CHECK_AUTH = 1;
  // 서버 도메인 : 백엔드 서버 주소와 프론트엔드 서버 주소가 다른 경우 명시
  const API = '';
  // 이메일 정규식
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  // 암호 정규식
  const pwdRegex = /^(?=.*[a-zA-Z])(?=.*[!@#$%^*+=-])(?=.*[0-9]).{8,20}$/;
  const pwdPlaceholder = '영문 숫자 특수기호 조합 8 ~ 20자리';

  // 서버에 전송할 사용자 성향 정보 형식
  const persona_data_params = {
    "investment_grade": "",
    "risk_tolerance": "",
    "investment_style": "",
    "preferred_sectors": "",
    "holding_period": "",
    "typical_behavior": "",
    "favorite_patterns": "",
    "specific_stocks": "",
    "analysis_tendency": "",
    "special_note": "",
    "lua_branch": ""
  };
  let personaList = [];

  const fnGetToken = () => {
    return localStorage.getItem("token");
  };

  const fnSetToken = (token) => {
    localStorage.setItem("token", token);
  };

  /**
   * 관리자 로그인 여부 조회
   */
  const fnCheckSession = () => {
    const token = fnGetToken();
    if (token) {
      const config = {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        }
      };
      const url = `${API}/me`;
      axios.post(url, {}, config)
        .then((res) => {
          const data = res.data;
          //if (console) console.log("통신결과 : ", res);
          if (data && data['email']) {
            fnOnLogin();
          } else {
            fnShowLogin();
          }
        })
        .catch((err) => {
          if (console) console.error(err);
          if (console) console.log('status : ' + err.response.status);
          fnShowLogin();
        });
    } else {
      fnShowLogin();
    }
  };

  /**
   * 관리자 로그인 양식 보이기
   */
  const fnShowLogin = () => {
    fnSetToken('');
    $('header .buttons').empty();
    const savedId = localStorage.getItem("saved_id");
    if ($('#root form[name="loginForm"] #login_id').length) {
      return;
    }
    let txt = '';
    txt += '<form name="loginForm">';
    txt += '<div class="min-w-full md:min-w-64 w-3/4 md:w-2/5 mx-auto mt-5 px-5 py-2 border border-gray-200 rounded-xl shadow-sm">';
    txt += '<div class="form-row flex items-center py-2">';
    txt += '<label for="login_id" class="w-1/3 flex-none">이메일</label>';
    txt += '<input type="email" id="login_id" name="login_id" class="flex-auto border border-gray-500 rounded-sm px-2 py-1" minlength="10" maxlength="50">';
    txt += '</div>';
    txt += '<div class="form-row flex items-center py-2">';
    txt += '<label for="login_pwd" class="w-1/3 flex-none">암호</label>';
    txt += '<input type="password" id="login_pwd" name="login_pwd" class="flex-auto border border-gray-500 rounded-sm px-2 py-1" minlength="8" maxlength="20">';
    txt += '</div>';
    txt += '<div class="flex items-center justify-between px-3 py-3">';
    txt += '<div>';
    txt += '<input type="checkbox" id="save_id" name="save_id">';
    txt += '<label for="save_id" class="ml-3 text-sm text-gray-700">이메일 저장</label>';
    txt += '</div>';
    txt += '<div>';
    txt += '<button type="button" class="btn-login px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-800 text-white transition-colors">로그인</button>';
    txt += '<button type="button" class="btn-signup ml-2 px-4 py-2 rounded-md bg-green-600 hover:bg-green-700 text-white transition-colors">관리자 등록</button>';
    txt += '<button type="button" class="btn-rigister px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-800 text-white transition-colors" style="display: none;">등록</button>';
    txt += '<button type="button" class="btn-cancel ml-2 px-4 py-2 rounded-md bg-gray-500 hover:bg-gray-600 text-white transition-colors" style="display: none;">취소</button>';
    txt += '</div>';
    txt += '</div>';
    txt += '</div>';
    txt += '</form>';
    $('#root').html(txt);
    
    $('#root form[name="loginForm"] #login_id').val(savedId ? savedId : '');
    $('#root form[name="loginForm"] #save_id').prop('checked', savedId ? true : false);
    if (console) console.log('#save_id checked : ' + $('#root form[name="loginForm"] #save_id').prop('checked'));

    $('#root form[name="loginForm"] #login_id').val(savedId ? savedId : '');
    $('#root form[name="loginForm"] #login_pwd').attr('placeholder', '').attr('autocomplete', 'current-password');
    $('#root form[name="loginForm"] button.btn-login').on('click', function() {
      fnLogin();
      return false;
    });
    $('#root form[name="loginForm"] button.btn-signup').on('click', function() {
      if ($('#root form[name="loginForm"] .form-row').length === 2 && $('#root form[name="loginForm"] input[name="login_name"]').length === 0) {
        let txt = '<div class="form-row flex items-center py-2">';
        txt += '<label for="login_name" class="w-1/3 flex-none">이름</label>';
        txt += '<input type="text" id="login_name" name="login_name" class="flex-auto border border-gray-500 rounded-sm px-2 py-1" maxlength="10">';
        txt += '</div>';
        $('#root form[name="loginForm"] .form-row').last().after($(txt));
      } else if ($('#root form[name="loginForm"] .form-row').length === 3) {
        $('#root form[name="loginForm"] .form-row').eq(2).show();
      }
      $('#root form[name="loginForm"] #login_pwd').attr('placeholder', pwdPlaceholder).attr('autocomplete', 'new-password');
      $('#root form[name="loginForm"] button.btn-login, #root form[name="loginForm"] button.btn-signup').hide();
      $('#root form[name="loginForm"] button.btn-rigister, #root form[name="loginForm"] button.btn-cancel').show();
      return false;
    });
    $('#root form[name="loginForm"] button.btn-cancel').on('click', function() {
      // 등록 취소
      $('#root form[name="loginForm"] #login_pwd').attr('placeholder', '').attr('autocomplete', 'current-password');
      $('#root form[name="loginForm"] button.btn-login, #root form[name="loginForm"] button.btn-signup').show();
      $('#root form[name="loginForm"] button.btn-rigister, #root form[name="loginForm"] button.btn-cancel').hide();
      if ($('#root form[name="loginForm"] .form-row').length === 3) {
        $('#root form[name="loginForm"] .form-row').eq(2).hide();
      }
      return false;
    });
    $('#root form[name="loginForm"] button.btn-rigister').on('click', function() {
      // 등록
      fnSignUp();
      return false;
    });
  };

  /**
   * 관리자 로그인 성공 후 처리할 작업
   */
  const fnOnLogin = () => {
    if ($('header .buttons button').length < 2) {
      let txt = '';
      txt += '<button type="button" class="btn-logout px-3 py-1 rounded-md bg-slate-100 hover:bg-slate-300 text-black transition-colors">로그아웃</button>';
      txt += '<button type="button" class="btn-change-pwd ml-2 px-3 py-1 rounded-md bg-slate-100 hover:bg-slate-300 text-black transition-colors">암호변경</button>';
      $('header .buttons').html(txt);
      $('header .buttons button.btn-logout').on('click', function() {
        // 로그아웃
        fnLogout();
        return false;
      });
      $('header .buttons button.btn-change-pwd').on('click', function() {
        // 암호변경
        fnShowChangePwd();
        return false;
      });
    }
    fnLoadList();
  };

  /**
   * 관리자 로그인
   */
  const fnLogin = () => {
    // 이메일
    const _email = $.trim($('#root form[name="loginForm"] #login_id').val());
    if (_email === '') {
      alert('이메일을 입력해 주세요.');
      return false;
    }
    // 암호
    const _password = $.trim($('#root form[name="loginForm"] #login_pwd').val());
    if (_password === '') {
      alert('암호를 입력해 주세요.');
      return false;
    }
    const params = {
      email: _email, 
      password: _password
    };
    const config = {
      headers: {
        'Content-Type': 'application/json'
      }
    };
    const url = `${API}/login`;
    axios.post(url, params, config)
      .then((res) => {
        const data = res.data;
        //if (console) console.log("통신결과 : ", res);
        //if (console) console.log(res.data);
        if (data.token) {
          const savedId = $('#root form[name="loginForm"] #save_id').prop('checked') ? _email : '';
          localStorage.setItem("saved_id", savedId);
          fnSetToken(data.token);
          fnOnLogin();
        } else {
          alert("로그인 실패");
        }
      })
      .catch((err) => {
        //if (console) console.error(err);
        //if (console) console.log(err.response);
        if (err.response && err.response.data && err.response.data.error) {
          alert(err.response.data.error);
        }
      });
  };

  /**
   * 관리자 로그아웃
   */
  const fnLogout = () => {
    fnShowLogin();
  };

  const fnCloseModalEtc = () => {
    // Hide modal with transition classes
    //$('#modal-etc').addClass('opacity-0');
    $('#modal-etc').removeClass('show').hide();

    $('#modal-etc .modal-title').empty();
    
    $('#modal-etc .modal-body form[name="modalForm"]').get(0).reset();

    // Wait for transition to end before making it non-interactive
    window.setTimeout(() => {
      $('body').removeClass('overflow-hidden');
    }, 300);
  };

  /**
   * 관리자 암호 변경
   */
  const fnShowChangePwd = () => {
    if ($('#modal-etc .modal-body form[name="modalForm"] #current_pwd').length === 0) {
      let txt = '';
      txt += '<form name="modalForm" class="overflow-x-auto">';
      txt += '<table class="min-w-full divide-y divide-gray-200">';
      txt += '<colgroup>';
      txt += '<col style="width:28%;">';
      txt += '</colgroup>';
      txt += '<tbody class="bg-white divide-y divide-gray-200">';
      txt += '<tr>';
      txt += '<th scope="row" class="py-3 font-semibold text-gray-500">현재 암호</th>';
      txt += '<td class="px-6 py-4 text-gray-600">';
      txt += '<input type="password" id="current_pwd" name="current_pwd" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" minlength="8" maxlength="20" autocomplete="current-password">';
      txt += '</td>';
      txt += '</tr>';
      txt += '<tr>';
      txt += '<th scope="row" class="py-3 font-semibold text-gray-500">새 암호</th>';
      txt += '<td class="px-6 py-4 text-gray-600">';
      txt += `<input type="password" id="new_pwd" name="new_pwd" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" minlength="8" maxlength="20" placeholder="${pwdPlaceholder}" autocomplete="new-password">`;
      txt += '</td>';
      txt += '</tr>';
      txt += '<tr>';
      txt += '<th scope="row" class="py-3 font-semibold text-gray-500">새 암호 확인</th>';
      txt += '<td class="px-6 py-4 text-gray-600">';
      txt += `<input type="password" id="confirm_pwd" name="confirm_pwd" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" minlength="8" maxlength="20" placeholder="${pwdPlaceholder}" autocomplete="new-password">`;
      txt += '</td>';
      txt += '</tr>';
      txt += '</tbody>';
      txt += '</table>';
      txt += '</form>';
      $('#modal-etc .modal-body').html(txt);

      //* 암호 변경
      $('#modal-etc .modal-buttons button.modal-confirm-button').on('click', function() {
        const token = fnGetToken();
        if (console) console.log("token : ", token);
        if (token) {
          // 암호
          const _current_password = $.trim($('#modal-etc .modal-body form[name="modalForm"] #current_pwd').val());
          //if (console) console.log(`현재 암호 : "${_current_password}"`);
          if (_current_password === '') {
            alert('현재 암호를 입력해 주세요.');
            return false;
          }
          const _new_password = $.trim($('#modal-etc .modal-body form[name="modalForm"] #new_pwd').val());
          if (_new_password === '') {
            alert('새 암호를 입력해 주세요.');
            return false;
          }
          if (!pwdRegex.test(_new_password)) {
            alert('새 암호 형식을 확인해 주세요.');
            return false;
          }
          const _confirm_password = $.trim($('#modal-etc .modal-body form[name="modalForm"] #confirm_pwd').val());
          if (_confirm_password === '') {
            alert('새 암호 확인을 입력해 주세요.');
            return false;
          }
          if (_confirm_password !== _new_password) {
            alert('새 암호와 새 암호 확인이 일치하지 않습니다.');
            return false;
          }
          const params = {
            current_password: _current_password,
            new_password: _new_password,
            confirm_password: _confirm_password,
          };
          const config = {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            }
          };
          const url = `${API}/change-passrod`;
          axios.post(url, params, config)
            .then((res) => {
              const data = res.data;
              //if (console) console.log("통신결과 : ", res);
              if (data.result > 0) {
                fnCloseModalEtc();
              } else {
                alert("오류가 발생했습니다.");
              }
            })
            .catch((err) => {
              //if (console) console.error(err);
              if (err.response && err.response.status === 403) {
                fnLogout();
              }
            });
        } else {
          fnLogout();
        }
        return false;
      });
    }

    $('#modal-etc .modal-title').html('관리자 암호 변경');
    
    // Show modal with transition classes
    $('#modal-etc').addClass('show').show();
    //$('#modal .modal-backdrop').removeClass('scale-95');
    $('body').addClass('overflow-hidden'); // Prevent background scroll
  };

  /**
   * 관리자 회원가입
   */
  const fnSignUp = () => {
    // 이메일
    const _email = $.trim($('#root form[name="loginForm"] #login_id').val());
    //if (console) console.log(`이메일 : "${_email}"`);
    if (_email === '') {
      alert('이메일을 입력해 주세요.');
      return false;
    }
    // regex.test(문자열) 메서드는 문자열이 정규식 패턴과 일치하면 true, 아니면 false를 반환합니다.
    //if (console) console.log(`emailRegex.test("${_email}") : ${emailRegex.test(_email)}`);
    if (!emailRegex.test(_email)) {
      alert('이메일 형식을 확인해 주세요.');
      return false;
    }
    // 암호
    const _password = $.trim($('#root form[name="loginForm"] #login_pwd').val());
    //if (console) console.log(`암호 : "${_password}"`);
    if (_password === '') {
      alert('암호를 입력해 주세요.');
      return false;
    }
    if (!pwdRegex.test(_password)) {
      alert('암호 형식을 확인해 주세요.');
      return false;
    }
    const _name = $.trim($('#root form[name="loginForm"] #login_name').val());
    if (_name === '') {
      alert('이름을 입력해 주세요.');
      return false;
    }
    const params = {
      email: _email, 
      password: _password, 
      name: _name
    };
    const config = {
      headers: {
        'Content-Type': 'application/json'
      }
    };
    const url = `${API}/signup`;
    axios.post(url, params, config)
      .then((res) => {
        const data = res.data;
        //if (console) console.log("통신결과 : ", res);
        //if (console) console.log(res.data);
        if (data.token) {
          fnSetToken(data.token);
          fnOnLogin();
        } else {
          alert("관리자 등록 실패");
        }
      })
      .catch((err) => {
        //if (console) console.error(err);
        //if (console) console.log(err.response);
        if (err.response && err.response.data && err.response.data.error) {
          alert(err.response.data.error);
        }
      });
  };

  const investment_items = [
    { "id": "1", "investment_grade": "1등급 (공격투자형)", "risk_tolerance": "고위험 고수익" },
    { "id": "2", "investment_grade": "2등급 (적극투자형)", "risk_tolerance": "중위험 중수익" },
    { "id": "3", "investment_grade": "3등급 (위험중립형)", "risk_tolerance": "중저위험" },
    { "id": "4", "investment_grade": "4등급 (안정추구형)", "risk_tolerance": "저위험" },
    { "id": "5", "investment_grade": "5등급 (안정형)", "risk_tolerance": "저위험 안정형" },
  ];

  const fnInitModal = () => {
    let txt = '';
    txt += '<form name="modalForm" class="overflow-x-auto">';
    txt += '<table class="min-w-full divide-y divide-gray-200">';
    txt += '<colgroup>';
    txt += '<col style="width:100px;">';
    txt += '</colgroup>';
    txt += '<tbody class="bg-white divide-y divide-gray-200">';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500 uppercase">user id</th>';
    txt += '<td class="px-6 py-4 font-mono font-bold text-blue-600"><span class="user_id"></span></td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">성별</th>';
    txt += '<td class="px-6 py-4 text-gray-600"><span class="gender"></span></td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">나이</th>';
    txt += '<td class="px-6 py-4 text-gray-600"><span class="age"></span></td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">페르소나</th>';
    txt += '<td class="px-6 py-4 text-gray-600"><span class="persona_name"></span></td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">투자 성향</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<select name="investment_grade" class="px-3 py-2 text-gray-600 border border-dark rounded-sm">';
    for (const option_item of investment_items) {
      txt += `<option value="${option_item['id']}">${option_item['investment_grade']}</option>`;
    }
    txt += '</select>';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">risk_tolerance</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="risk_tolerance" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">investment_style</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="investment_style" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">preferred_sectors</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="preferred_sectors" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '<div class="text-sm text-red-700">* 쉼표(,)로 구분</div>';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">holding_period</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="holding_period" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">typical_behavior</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="typical_behavior" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">favorite_patterns</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="favorite_patterns" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '<div class="text-sm text-red-700">* 쉼표(,)로 구분</div>';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">specific_stocks</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="specific_stocks" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '<div class="text-sm text-red-700">* 쉼표(,)로 구분</div>';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">analysis_tendency</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="analysis_tendency" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">special_note</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="special_note" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '</td>';
    txt += '</tr>';
    txt += '<tr>';
    txt += '<th scope="row" class="py-3 font-semibold text-gray-500">lua_branch</th>';
    txt += '<td class="px-6 py-4 text-gray-600">';
    txt += '<input name="lua_branch" class="w-full px-3 py-2 text-gray-600 border border-dark rounded-sm" value="">';
    txt += '</td>';
    txt += '</tr>';
    txt += '</tbody>';
    txt += '</table>';
    txt += '</form>';
    $('#modal .modal-body').html(txt);

    $('#modal .modal-body select[name="investment_grade"]').on('change', function() {
      const _id = $.trim(this.value);
      for (const option_item of investment_items) {
        if (option_item['id'] === _id) {
          $('#modal .modal-body input[name="risk_tolerance"]').val(option_item['risk_tolerance']);
          break;
        }
      }
    });
    //* 저장
    $('#modal .modal-buttons button.modal-confirm-button').on('click', function() {
      const token = fnGetToken();
      if (CHECK_AUTH === 0 || token) {
        const user_id = $.trim($('#modal .modal-body .user_id').text());
        let msg = user_id;
        msg += ' [' + $.trim($('#modal .modal-body .persona_name').text()) + ']';
        msg += ' 사용자의 투자 성향을 수정하시겠습니까?'
        if (confirm(msg)) {
          let _id = '';
          for (const item of personaList) {
            if (item['user_id'] === user_id) {
              _id = item['_id'];
              const investment_grade_id = $.trim($('#modal .modal-body select[name="investment_grade"]').val());
              for (const option_item of investment_items) {
                if (option_item['id'] === investment_grade_id) {
                  persona_data_params["investment_grade"] = option_item['investment_grade'];
                  break;
                }
              }
              persona_data_params["risk_tolerance"] = $.trim($('#modal .modal-body input[name="risk_tolerance"]').val());
              persona_data_params["investment_style"] = $.trim($('#modal .modal-body input[name="investment_style"]').val());
              let preferred_sectors = $.trim($('#modal .modal-body input[name="preferred_sectors"]').val()).split(',');
              for (let i = 0; i < preferred_sectors.length; i++) {
                preferred_sectors[i] = $.trim(preferred_sectors[i]);
              }
              persona_data_params["preferred_sectors"] =  preferred_sectors.join(',');
              persona_data_params["holding_period"] = $.trim($('#modal .modal-body input[name="holding_period"]').val());
              persona_data_params["typical_behavior"] = $.trim($('#modal .modal-body input[name="typical_behavior"]').val());
              let favorite_patterns = $.trim($('#modal .modal-body input[name="favorite_patterns"]').val()).split(',');
              for (let i = 0; i < favorite_patterns.length; i++) {
                favorite_patterns[i] = $.trim(favorite_patterns[i]);
              }
              persona_data_params["favorite_patterns"] =  favorite_patterns.join(',');
              let specific_stocks = $.trim($('#modal .modal-body input[name="specific_stocks"]').val()).split(',');
              for (let i = 0; i < specific_stocks.length; i++) {
                specific_stocks[i] = $.trim(specific_stocks[i]);
              }
              persona_data_params["specific_stocks"] =  specific_stocks.join(',');
              persona_data_params["analysis_tendency"] = $.trim($('#modal .modal-body input[name="analysis_tendency"]').val());
              persona_data_params["special_note"] = $.trim($('#modal .modal-body input[name="special_note"]').val());
              persona_data_params["lua_branch"] = $.trim($('#modal .modal-body input[name="lua_branch"]').val());
              break;
            }
          }

          if (_id) {
            // 서버에 전송
            const config = {
              headers: {
                'Content-Type': 'application/json'
              }
            };
            if (CHECK_AUTH > 0 && token) {
              config.headers['Authorization'] = `Bearer ${token}`;
            }
            const params = {
              id: _id, 
              persona_data: persona_data_params
              //persona_data: JSON.stringify(persona_data_params)
            };
            const url = `${API}/user/persona/register`; // /${_id}
            axios.post(url, params, config)
              .then((res) => {
                //if (console) console.log("통신결과 : ", res);
                if (res.status === 200) {
                  const data = res.data;
                  //if (console) console.log(res.data);
                  if (data.result > 0) {
                    // 수정된 데이터 반영
                    for (const item of personaList) {
                      if (item['user_id'] === user_id) {
                        item["investment_grade"] = persona_data_params['investment_grade'];
                        $('#root table tbody tr#row_' + user_id + ' td').eq(4).text(item["investment_grade"]);
                        item["risk_tolerance"] = persona_data_params["risk_tolerance"];
                        item["investment_style"] = persona_data_params["investment_style"];
                        item["preferred_sectors"] = persona_data_params["preferred_sectors"];
                        item["holding_period"] = persona_data_params["holding_period"];
                        item["typical_behavior"] = persona_data_params["typical_behavior"];
                        item["favorite_patterns"] = persona_data_params["favorite_patterns"];
                        item["specific_stocks"] = persona_data_params["specific_stocks"];
                        item["analysis_tendency"] = persona_data_params["analysis_tendency"];
                        item["special_note"] = persona_data_params["special_note"];
                        item["lua_branch"] = persona_data_params["lua_branch"];
                        break;
                      }
                    }
                    fnCloseModal();
                  } else {
                    alert("오류가 발생했습니다.");
                  }
                } else {
                  alert(res.message);
                }
              })
              .catch((err) => {
                //if (console) console.error(err);
                //if (console) console.log('status : ' + err.response.status);
                if (err.response && err.response.status === 403) {
                  fnLogout();
                }
              });
          }
        }
      } else {
        fnLogout();
      }
      return false;
    });
    //*/
  };

  const fnOpenModal = (item) => {
    //console.log(`openModal('${categoryId}', ${index})`);
    if (!item) {
      return;
    }

    let txt = '';
    txt = `<span class="font-mono font-bold text-blue-600">${item['user_id']}</span>`;
    txt += ` <span class="text-gray-600">${item['persona_name']}</span>`;
    $('#modal .modal-title').html(txt);
    
    $('#modal .modal-body .user_id').text(item['user_id']);
    $('#modal .modal-body .gender').text(item['gender']);
    $('#modal .modal-body .age').text(item['age']);
    $('#modal .modal-body .persona_name').text(item['persona_name']);
    for (const option_item of investment_items) {
      //if (console) console.log(`"${option_item['investment_grade']}" == "${item['investment_grade']}" : ${(option_item['investment_grade'] === item['investment_grade'])}`);
      if (option_item['investment_grade'] === item['investment_grade']) {
        $('#modal .modal-body select[name="investment_grade"]').val(option_item['id']);
        break;
      }
    }
    $('#modal .modal-body input[name="risk_tolerance"]').val(item['risk_tolerance']);
    $('#modal .modal-body input[name="investment_style"]').val(item['investment_style']);
    $('#modal .modal-body input[name="preferred_sectors"]').val(item['preferred_sectors'].join(','));
    $('#modal .modal-body input[name="holding_period"]').val(item['holding_period']);
    $('#modal .modal-body input[name="typical_behavior"]').val(item['typical_behavior']);
    $('#modal .modal-body input[name="favorite_patterns"]').val(item['favorite_patterns'].join(','));
    $('#modal .modal-body input[name="specific_stocks"]').val(item['specific_stocks'].join(','));
    $('#modal .modal-body input[name="analysis_tendency"]').val(item['analysis_tendency']);
    $('#modal .modal-body input[name="special_note"]').val(item['special_note']);
    $('#modal .modal-body input[name="lua_branch"]').val(item['lua_branch']);

    // Show modal with transition classes
    $('#modal').addClass('show').show();
    //$('#modal .modal-backdrop').removeClass('scale-95');
    $('body').addClass('overflow-hidden'); // Prevent background scroll
  };

  const fnCloseModal = () => {
    // Hide modal with transition classes
    //$('#modal').addClass('opacity-0');
    $('#modal').removeClass('show').hide();

    $('#modal .modal-title').empty();
    
    $('#modal .modal-body .user_id').empty();
    $('#modal .modal-body .gender').empty();
    $('#modal .modal-body .age').empty();
    $('#modal .modal-body .persona_name').empty();
    $('#modal .modal-body form[name="modalForm"]').get(0).reset();

    // Wait for transition to end before making it non-interactive
    window.setTimeout(() => {
      $('body').removeClass('overflow-hidden');
    }, 300);
  };

  /**
   * 사용자 성향 목록 조회
   */
  const fnLoadList = () => {
    const token = fnGetToken();
    if (CHECK_AUTH === 0 || token) {
      const config = {
        headers: {
          'Content-Type': 'application/json',
        }
      };
      if (CHECK_AUTH > 0 && token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      const url = `${API}/user/persona/list`;
      axios.post(url, {}, config)
        .then((res) => {
          const list = res.data;
          //if (console) console.log("통신결과 : ", res);
          personaList = list;
          fnGeneratePersonaList();
        })
        .catch((err) => {
          //if (console) console.error(err);
          //if (console) console.log('status : ' + err.response.status);
          if (err.response && err.response.status === 403) {
            fnLogout();
          }
        });
    } else {
      fnLogout();
    }
  };

  const fnGeneratePersonaList = () => {
    let txt = '';
    txt += '<div class="overflow-x-auto">'
    txt += '<div class="py-3 px-2 font-bold text-gray-900">사용자 성향 목록</div>'
    txt += '<table class="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-xl shadow-sm">';
    txt += '<thead class="bg-gray-50">';
    txt += '<tr>';
    txt += '<th scope="col" class="px-6 py-3 font-semibold text-gray-500 uppercase">user id</th>';
    txt += '<th scope="col" class="px-6 py-3 font-semibold text-gray-500">성별</th>';
    txt += '<th scope="col" class="px-6 py-3 font-semibold text-gray-500">나이</th>';
    txt += '<th scope="col" class="px-6 py-3 font-semibold text-gray-500">페르소나</th>';
    txt += '<th scope="col" class="px-6 py-3 font-semibold text-gray-500">투자 성향</th>';
    txt += '<th class="px-6 py-3 font-semibold text-gray-500"></th>';
    txt += '</tr>';
    txt += '</thead>';
    txt += '<tbody class="bg-white divide-y divide-gray-200">';
    if (personaList && personaList.length) {
      for (const item of personaList) {
        txt += `<tr id="row_${item['user_id']}">`;
        txt += `<td class="px-6 py-4 text-center"><button type="button" class="btn-modify font-mono font-bold text-blue-600 underline border-0" data-id="${item['user_id']}">${item['user_id']}</button></td>`;
        txt += `<td class="px-6 py-4 text-center text-gray-600">${item['gender']}</td>`;
        txt += `<td class="px-6 py-4 text-center text-gray-600">${item['age']}</td>`;
        txt += `<td class="px-6 py-4 text-center text-gray-600">${item['persona_name']}</td>`;
        txt += `<td class="px-6 py-4 text-center text-gray-600">${item['investment_grade']}</td>`;
        txt += `<td class="px-6 py-4 text-center text-gray-600"><button type="button" class="btn-train px-4 py-2 rounded-md text-white bg-pink-500 hover:bg-pink-700 transition-colors" data-id="${item['user_id']}">봇 학습</button></td>`;
        txt += '</tr>';
      }
    } else {
      txt += '<tr>';
      txt += '<td colspan="6" class="px-6 py-4 text-center text-gray-600">조회된 데이터가 없습니다.</td>';
      txt += '</tr>';
    }
    txt += '</tbody>';
    txt += '</table>';
    txt += '</div>'
    $('#root').html(txt);
    // 관리 모달 열기
    $('button.btn-modify').on('click', function() {
      const user_id = $.trim($(this).attr('data-id'));
      for (const item of personaList) {
        if (item['user_id'] === user_id) {
          fnOpenModal(item);
          break;
        }
      }
      return false;
    });
    /* 봇 학습
    $('button.btn-train').on('click', function() {
      const user_id = $.trim($(this).attr('data-id'));
      for (const item of personaList) {
        if (item['user_id'] === user_id) {
          //봇 학습
          break;
        }
      }
      return false;
    });
    //*/
  };

  $('#modal .modal-close-button, #modal .modal-cancel-button').on('click', function(e) {
    e.stopPropagation();
    fnCloseModal();
    return false;
  });

  $('#modal-etc .modal-close-button, #modal-etc .modal-cancel-button').on('click', function(e) {
    e.stopPropagation();
    fnCloseModalEtc();
    return false;
  });

  fnInitModal();
  if (CHECK_AUTH > 0) {
    fnCheckSession();
  } else {
    fnLoadList();
  }
})